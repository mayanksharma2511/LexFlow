"""Calls to the language model (through the Groq API).

Long documents are read in full: they are split into overlapping sections that fit the
model's limits, each section is analysed, and the results are combined. Calls are paced to
stay under the account's tokens-per-minute limit, so on Groq's free tier a long contract
takes a minute or more rather than failing.

Clauses and risks must come with a word-for-word quote, which is checked against the
document (grounding.py) before it is shown.
"""

import difflib
import json
import logging
import re
import threading
import time
from collections import deque
from typing import Any

from groq import APIConnectionError, APIError, Groq, RateLimitError

from app.core.config import settings
from app.core.exceptions import (
    LLMConnectionError,
    LLMQuotaExceededError,
    LLMRateLimitError,
    LLMServiceError,
)
from app.services.ai.grounding import normalize, verify_quote
from app.services.ai.prompts import (
    CASE_SYNTHESIS_PROMPT,
    CLASSIFICATION_PROMPT,
    CLAUSE_EXTRACTION_PROMPT,
    CLAUSE_TYPES,
    COMPARISON_SUMMARY_PROMPT,
    RISK_ANALYSIS_PROMPT,
    SECTION_NOTES_PROMPT,
    SUMMARY_PROMPT,
)

logger = logging.getLogger(__name__)

client = Groq(api_key=settings.GROQ_API_KEY or "missing", max_retries=0, timeout=120)

SECTION_OVERLAP_CHARS = 600          # so a clause cut at a section boundary is seen whole once
MAX_SECTIONS_IN_APP = 12             # about 190,000 characters; longer documents are read in part
CLASSIFICATION_CHARS = 6000          # the document type is clear from the start of a document
MAX_OUTPUT_TOKENS = 2000
CHARS_PER_TOKEN = 3.5                # rough estimate used only for pacing
MAX_RATE_LIMIT_RETRIES = 4


class _Pacer:
    """Keeps the estimated tokens sent in any 60-second window under the per-minute limit."""

    def __init__(self, tokens_per_minute: int) -> None:
        self.budget = int(tokens_per_minute * 0.9)
        self.sent: deque[tuple[float, int]] = deque()
        self.lock = threading.Lock()

    def wait_for(self, tokens: int) -> None:
        tokens = min(tokens, self.budget)
        while True:
            with self.lock:
                now = time.monotonic()
                while self.sent and now - self.sent[0][0] >= 60:
                    self.sent.popleft()
                used = sum(t for _, t in self.sent)
                if used + tokens <= self.budget:
                    self.sent.append((now, tokens))
                    return
                wait = 60 - (now - self.sent[0][0]) + 0.5
            time.sleep(max(wait, 0.5))


pacer = _Pacer(settings.LLM_TOKENS_PER_MINUTE)


def _parse_json(content: str | None, task: str) -> dict:
    """Parse the model's JSON reply. An unreadable reply is treated as a failure (the caller
    then shows that the analysis is unavailable) rather than replaced with made-up values."""
    try:
        parsed = json.loads(content or "")
    except json.JSONDecodeError as exc:
        raise LLMServiceError(f"The AI returned an unreadable {task} result.") from exc
    if not isinstance(parsed, dict):
        raise LLMServiceError(f"The AI returned an unexpected {task} result.")
    return parsed


def split_into_sections(text: str, size: int | None = None, overlap: int = SECTION_OVERLAP_CHARS) -> list[tuple[int, str]]:
    """Split text into overlapping sections of about `size` characters, preferring to cut at a
    paragraph or sentence break. Returns (start offset, section text) pairs covering the whole text."""
    size = size or settings.LLM_SECTION_CHARS
    text = text or ""
    if len(text) <= size:
        return [(0, text)] if text.strip() else []
    sections: list[tuple[int, str]] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            window = text[start + size // 2:end]
            cut = max(window.rfind("\n\n"), window.rfind(". "), window.rfind("\n"))
            if cut > 0:
                end = start + size // 2 + cut + 1
        sections.append((start, text[start:end]))
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return sections


def _coverage(text: str, sections: list[tuple[int, str]], read: list[tuple[int, str]]) -> dict[str, int]:
    last = read[-1] if read else (0, "")
    return {
        "characters": len(text),
        "characters_read": min(len(text), last[0] + len(last[1])),
        "sections": len(sections),
        "sections_read": len(read),
    }


def _verify_items(items: list[dict], text: str) -> list[dict]:
    """Attach a verification status to each item's quote and drop exact duplicates."""
    doc = normalize(text)
    seen: set[tuple[str, str]] = set()
    verified: list[dict] = []
    for item in items:
        quote = str(item.get("quote") or "").strip()
        key = (str(item.get("type") or item.get("title") or ""), normalize(quote)[:200])
        if not quote or key in seen:
            continue
        seen.add(key)
        check = verify_quote(quote, text, doc)
        verified.append({**item, "quote": quote, "verification": check["status"], "match_score": check["score"]})
    return verified


def _risk_level(score: int) -> str:
    if score >= 67:
        return "High"
    if score >= 34:
        return "Medium"
    return "Low"


class LLMService:

    def _execute_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0,
        json_mode: bool = False,
        max_output_tokens: int = MAX_OUTPUT_TOKENS,
    ) -> str:
        """Call the model, pacing to the per-minute limit and waiting when rate-limited."""
        prompt_chars = sum(len(m["content"]) for m in messages)
        estimate = int(prompt_chars / CHARS_PER_TOKEN) + max_output_tokens // 2
        kwargs: dict[str, Any] = {
            "model": settings.LLM_MODEL,
            "temperature": temperature,
            "messages": messages,
            "max_completion_tokens": max_output_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        if settings.LLM_MODEL.startswith("openai/gpt-oss"):
            kwargs["extra_body"] = {"reasoning_effort": "low"}

        if not settings.GROQ_API_KEY:
            raise LLMServiceError("No GROQ_API_KEY is configured, so AI analysis is unavailable.")

        for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
            pacer.wait_for(estimate)
            try:
                response = client.chat.completions.create(**kwargs)
                return response.choices[0].message.content or ""
            except RateLimitError as exc:
                retry_after = 20.0
                try:
                    retry_after = float(exc.response.headers.get("retry-after", retry_after))
                except (AttributeError, TypeError, ValueError):
                    pass
                body = str(exc).lower()
                if "per day" in body or "tokens per day" in body or "(tpd)" in body or "(rpd)" in body:
                    raise LLMQuotaExceededError("The AI service's daily limit has been reached. Try again tomorrow.") from exc
                logger.warning("Rate limited (attempt %d); waiting %.0fs", attempt + 1, retry_after)
                if attempt == MAX_RATE_LIMIT_RETRIES:
                    raise LLMRateLimitError("The AI service is busy. Please retry shortly.") from exc
                time.sleep(min(retry_after, 60))
            except APIConnectionError as exc:
                if attempt == MAX_RATE_LIMIT_RETRIES:
                    raise LLMConnectionError("Could not connect to the AI service.") from exc
                time.sleep(2)
            except APIError as exc:
                raise LLMServiceError(f"AI service error: {exc}") from exc
        raise LLMServiceError("The AI service did not respond.")

    def _sections_for_app(self, text: str) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
        sections = split_into_sections(text)
        return sections, sections[:MAX_SECTIONS_IN_APP]

    # ----- Summary -----

    def summarize(self, text: str) -> str:
        sections, read = self._sections_for_app(text)
        if not read:
            return "No text could be extracted from this document."
        if len(read) == 1:
            summary = self._execute_completion(
                [{"role": "system", "content": SUMMARY_PROMPT}, {"role": "user", "content": read[0][1]}],
                temperature=0.2,
            )
        else:
            notes = []
            for i, (_, section) in enumerate(read, start=1):
                note = self._execute_completion(
                    [{"role": "system", "content": SECTION_NOTES_PROMPT}, {"role": "user", "content": section}],
                    temperature=0.2, max_output_tokens=800,
                )
                notes.append(f"Section {i}:\n{note}")
            summary = self._execute_completion(
                [{"role": "system", "content": SUMMARY_PROMPT}, {"role": "user", "content": "\n\n".join(notes)}],
                temperature=0.2,
            )
        cov = _coverage(text, sections, read)
        read_note = (
            f"Read the whole document ({cov['characters']:,} characters, {cov['sections']} section(s))."
            if cov["sections_read"] == cov["sections"]
            else f"Read the first {cov['characters_read']:,} of {cov['characters']:,} characters."
        )
        return f"{summary}\n\n_{read_note}_"

    # ----- Classification -----

    def classify_document(self, text: str) -> dict:
        content = self._execute_completion(
            [{"role": "system", "content": CLASSIFICATION_PROMPT}, {"role": "user", "content": text[:CLASSIFICATION_CHARS]}],
            json_mode=True, max_output_tokens=400,
        )
        return _parse_json(content, "classification")

    # ----- Clause extraction -----

    def extract_clauses_from_sections(self, text: str, sections: list[tuple[int, str]]) -> tuple[list[str], list[dict]]:
        """Run the clause prompt on each section; return (parties, verified clauses)."""
        parties: list[str] = []
        clauses: list[dict] = []
        for _, section in sections:
            result = _parse_json(self._execute_completion(
                [{"role": "system", "content": CLAUSE_EXTRACTION_PROMPT}, {"role": "user", "content": section}],
                json_mode=True,
            ), "clause extraction")
            for party in result.get("parties") or []:
                name = str(party).strip()
                if name and name not in parties:
                    parties.append(name)
            for clause in result.get("clauses") or []:
                if isinstance(clause, dict) and clause.get("type") in CLAUSE_TYPES:
                    clauses.append({
                        "type": clause["type"],
                        "quote": str(clause.get("quote") or ""),
                        "explanation": str(clause.get("explanation") or ""),
                    })
        return parties, _verify_items(clauses, text)

    def extract_clauses(self, text: str) -> dict:
        sections, read = self._sections_for_app(text)
        classification = self.classify_document(text)
        parties, clauses = self.extract_clauses_from_sections(text, read)
        return {
            "document_type": classification.get("document_type", "Other"),
            "confidence": classification.get("confidence"),
            "data": {
                "parties": parties,
                "clauses": clauses,
                "coverage": _coverage(text, sections, read),
            },
        }

    # ----- Risk analysis -----

    def analyze_risks(self, text: str) -> dict:
        sections, read = self._sections_for_app(text)
        risks: list[dict] = []
        scores: list[int] = []
        for _, section in read:
            result = _parse_json(self._execute_completion(
                [{"role": "system", "content": RISK_ANALYSIS_PROMPT}, {"role": "user", "content": section}],
                json_mode=True,
            ), "risk analysis")
            try:
                scores.append(max(0, min(100, int(result.get("risk_score") or 0))))
            except (TypeError, ValueError):
                pass
            for risk in result.get("risks") or []:
                if isinstance(risk, dict):
                    risks.append({
                        "title": str(risk.get("title") or "Untitled"),
                        "severity": str(risk.get("severity") or "Low").capitalize(),
                        "description": str(risk.get("description") or ""),
                        "quote": str(risk.get("quote") or ""),
                    })
        score = max(scores) if scores else 0
        return {
            "risk_score": score,
            "risk_level": _risk_level(score),
            "risks": _verify_items(risks, text),
            "coverage": _coverage(text, sections, read),
            "note": "The score is the AI's judgement for the most concerning section (0-100); "
                    "Low is below 34, Medium 34-66, High 67 or more.",
        }

    # ----- Comparison -----

    def _normalize_comparison_result(
        self,
        raw_result: dict,
        default_summary: str = "Document comparison complete.",
    ) -> dict[str, Any]:
        """Ensures comparison results strictly adhere to ComparisonResponse schema fields."""
        summary = str(raw_result.get("summary") or default_summary)

        def _clean_changes(items: Any) -> list[dict[str, str]]:
            if not isinstance(items, list):
                return []
            cleaned = []
            for item in items:
                if isinstance(item, dict):
                    cleaned.append({"old": str(item.get("old", "")), "new": str(item.get("new", ""))})
                elif isinstance(item, str):
                    cleaned.append({"old": "", "new": item})
            return cleaned

        added = _clean_changes(raw_result.get("added"))
        removed = _clean_changes(raw_result.get("removed"))
        modified = _clean_changes(raw_result.get("modified"))
        if not (added or removed or modified):
            diffs = raw_result.get("differences") or raw_result.get("changes")
            if isinstance(diffs, list):
                modified = _clean_changes(diffs)
        return {"summary": summary, "added": added, "removed": removed, "modified": modified}

    @staticmethod
    def diff_documents(old_text: str, new_text: str, limit: int = 50) -> dict[str, list[dict[str, str]]]:
        """Find added, removed and changed sentences with a text comparison (no AI involved),
        so every listed change really is in the documents."""
        def sentences(text: str) -> list[str]:
            flat = re.sub(r"\s+", " ", text or "").strip()
            return [s for s in re.split(r"(?<=[.;:])\s+(?=[A-Z0-9(\"'])", flat) if s]

        old, new = sentences(old_text), sentences(new_text)
        added: list[dict[str, str]] = []
        removed: list[dict[str, str]] = []
        modified: list[dict[str, str]] = []
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
            if op == "insert":
                added.extend({"old": "", "new": s} for s in new[j1:j2])
            elif op == "delete":
                removed.extend({"old": s, "new": ""} for s in old[i1:i2])
            elif op == "replace":
                # Pair each old sentence with its most similar new one; unpaired sentences
                # were removed or added rather than changed.
                unused = list(range(j1, j2))
                for i in range(i1, i2):
                    best, best_ratio = None, 0.0
                    for j in unused:
                        ratio = difflib.SequenceMatcher(None, old[i], new[j]).ratio()
                        if ratio > best_ratio:
                            best, best_ratio = j, ratio
                    if best is not None and best_ratio >= 0.6:
                        modified.append({"old": old[i], "new": new[best]})
                        unused.remove(best)
                    else:
                        removed.append({"old": old[i], "new": ""})
                added.extend({"old": "", "new": new[j]} for j in unused)
        return {"added": added[:limit], "removed": removed[:limit], "modified": modified[:limit]}

    def compare_documents(self, old_text: str, new_text: str) -> dict:
        changes = self.diff_documents(old_text, new_text)
        counts = f"{len(changes['added'])} added, {len(changes['removed'])} removed and {len(changes['modified'])} changed passage(s)"
        if not any(changes.values()):
            return {"summary": "No differences were found between the two documents.", **changes}

        lines = [f"ADDED: {c['new']}" for c in changes["added"]]
        lines += [f"REMOVED: {c['old']}" for c in changes["removed"]]
        lines += [f"CHANGED FROM: {c['old']}\nCHANGED TO: {c['new']}" for c in changes["modified"]]
        payload = "\n\n".join(lines)
        partial = len(payload) > settings.LLM_SECTION_CHARS
        try:
            summary = self._execute_completion(
                [{"role": "system", "content": COMPARISON_SUMMARY_PROMPT},
                 {"role": "user", "content": payload[: settings.LLM_SECTION_CHARS]}],
                max_output_tokens=800,
            )
            if partial:
                summary += "\n\n(The summary covers the first part of the changes; all changes are listed below.)"
        except LLMServiceError as exc:
            logger.warning("Comparison summary unavailable: %s", exc)
            summary = f"Found {counts}. The AI summary is unavailable, but the changes below come directly from the documents."
        return {"summary": summary, **changes}

    # ----- Case synthesis -----

    def synthesize_case(self, case_title: str, document_summaries: list[tuple[str, str]]) -> dict:
        combined = "\n\n".join(f"--- {name} ---\n{summary}" for name, summary in document_summaries)
        content = self._execute_completion(
            [{"role": "system", "content": CASE_SYNTHESIS_PROMPT},
             {"role": "user", "content": f"CASE: {case_title}\n\n{combined[: settings.LLM_SECTION_CHARS]}"}],
            json_mode=True,
        )
        return _parse_json(content, "case synthesis")


llm_service = LLMService()
