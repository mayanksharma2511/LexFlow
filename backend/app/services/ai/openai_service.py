import json
import logging
import time
from typing import Any

from groq import APIConnectionError, APIError, Groq, RateLimitError

from app.core.config import settings
from app.core.exceptions import (
    LLMConnectionError,
    LLMQuotaExceededError,
    LLMRateLimitError,
    LLMServiceError,
)
from app.services.ai.prompts import (
    CASE_SYNTHESIS_PROMPT,
    CLASSIFICATION_PROMPT,
    DOCUMENT_COMPARISON_PROMPT,
    EMPLOYMENT_PROMPT,
    GENERIC_EXTRACTION_PROMPT,
    LEASE_PROMPT,
    NDA_PROMPT,
    RISK_ANALYSIS_PROMPT,
    SUMMARY_PROMPT,
)

logger = logging.getLogger(__name__)

client = Groq(
    api_key=settings.GROQ_API_KEY,
)

MAX_INPUT_CHARACTERS = 7000  # Safe window to fit within Groq TPM/RPM limits for scanned OCR text


def truncate_for_llm(text: str, max_chars: int = MAX_INPUT_CHARACTERS) -> str:
    """Window long or scanned OCR text to ensure it stays within Groq LLM token limits."""
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    head_len = max_chars // 2
    tail_len = max_chars // 2
    return f"{text[:head_len]}\n\n[... OCR TEXT TRUNCATED FOR TOKEN LIMITS ...]\n\n{text[-tail_len:]}"


class OpenAIService:

    def _execute_completion(self, messages: list[dict[str, str]], temperature: float = 0, json_mode: bool = False, max_retries: int = 2) -> str:
        """Internal execution helper wrapping LLM API calls with retry and exception classification."""
        last_exc: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                kwargs: dict[str, Any] = {
                    "model": "llama-3.1-8b-instant",
                    "temperature": temperature,
                    "messages": messages,
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}

                response = client.chat.completions.create(**kwargs)
                return response.choices[0].message.content or ""

            except RateLimitError as exc:
                last_exc = exc
                logger.warning("Groq/LLM Rate Limit Error (attempt %d/%d): %s", attempt + 1, max_retries + 1, exc)
                if attempt < max_retries:
                    time.sleep(1.2 * (attempt + 1))
                    continue
                raise LLMRateLimitError("LLM API rate limit exceeded. Please retry shortly.") from exc

            except APIConnectionError as exc:
                last_exc = exc
                logger.warning("Groq/LLM Connection Error (attempt %d/%d): %s", attempt + 1, max_retries + 1, exc)
                if attempt < max_retries:
                    time.sleep(1.0)
                    continue
                raise LLMConnectionError("Failed to connect to LLM service endpoint.") from exc

            except APIError as exc:
                logger.error("Groq/LLM API Error: %s", exc)
                if "quota" in str(exc).lower() or "limit" in str(exc).lower() or "429" in str(exc):
                    raise LLMQuotaExceededError("LLM API quota exceeded.") from exc
                raise LLMServiceError(f"LLM API Error: {exc}") from exc

            except Exception as exc:
                logger.exception("Unexpected error in LLM completion call")
                if "rate" in str(exc).lower() or "429" in str(exc):
                    raise LLMRateLimitError("LLM rate limit reached.") from exc
                raise LLMServiceError(f"LLM execution error: {exc}") from exc

        raise LLMServiceError(f"LLM execution failed after retries: {last_exc}")

    def summarize(
        self,
        text: str,
    ) -> str:
        safe_text = truncate_for_llm(text)
        messages = [
            {"role": "system", "content": SUMMARY_PROMPT},
            {"role": "user", "content": safe_text},
        ]
        return self._execute_completion(messages, temperature=0.2)

    def classify_document(
        self,
        text: str,
    ) -> dict:
        safe_text = truncate_for_llm(text)
        messages = [
            {"role": "system", "content": CLASSIFICATION_PROMPT},
            {"role": "user", "content": safe_text},
        ]
        content = self._execute_completion(messages, temperature=0, json_mode=True)
        try:
            return json.loads(content or "{}")
        except json.JSONDecodeError:
            return {"document_type": "Other", "confidence": 50}

    def extract_clauses(
        self,
        text: str,
    ) -> dict:
        safe_text = truncate_for_llm(text)
        classification = self.classify_document(safe_text)

        document_type = classification.get(
            "document_type",
            "Unknown",
        )

        prompt = GENERIC_EXTRACTION_PROMPT

        if document_type == "Employment Contract":
            prompt = EMPLOYMENT_PROMPT
        elif document_type == "Lease Agreement":
            prompt = LEASE_PROMPT
        elif document_type == "NDA":
            prompt = NDA_PROMPT

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": safe_text},
        ]

        content = self._execute_completion(messages, temperature=0, json_mode=True)
        try:
            result = json.loads(content or "{}")
        except json.JSONDecodeError:
            result = {}

        # Normalize parties into a simple list of strings.
        parties = result.get("parties", [])

        if isinstance(parties, list):
            flattened = []
            for party in parties:
                if isinstance(party, str):
                    flattened.append(party)
                elif isinstance(party, dict):
                    flattened.extend(
                        str(value)
                        for value in party.values()
                    )
            result["parties"] = flattened

        result["document_type"] = document_type
        result["confidence"] = classification.get(
            "confidence",
            0,
        )

        final_result = {
            "document_type": document_type,
            "confidence": classification.get(
                "confidence",
                0,
            ),
            "data": {
                key: value
                for key, value in result.items()
                if key not in {
                    "document_type",
                    "confidence",
                }
            },
        }

        return final_result

    def analyze_risks(
        self,
        text: str,
    ) -> dict:
        safe_text = truncate_for_llm(text)
        messages = [
            {"role": "system", "content": RISK_ANALYSIS_PROMPT},
            {"role": "user", "content": safe_text},
        ]
        content = self._execute_completion(messages, temperature=0, json_mode=True)
        try:
            return json.loads(content or "{}")
        except json.JSONDecodeError:
            return {"risk_score": 0, "risk_level": "Low", "risks": []}

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
                    cleaned.append({
                        "old": str(item.get("old", "")),
                        "new": str(item.get("new", "")),
                    })
                elif isinstance(item, str):
                    cleaned.append({"old": "", "new": item})
            return cleaned

        added = _clean_changes(raw_result.get("added"))
        removed = _clean_changes(raw_result.get("removed"))
        modified = _clean_changes(raw_result.get("modified"))

        # Fallback mapping if model used 'differences' or 'changes' array instead
        if not (added or removed or modified):
            diffs = raw_result.get("differences") or raw_result.get("changes")
            if isinstance(diffs, list):
                modified = _clean_changes(diffs)

        return {
            "summary": summary,
            "added": added,
            "removed": removed,
            "modified": modified,
        }

    def compare_documents(
        self,
        old_text: str,
        new_text: str,
    ) -> dict:
        safe_old = truncate_for_llm(old_text, max_chars=3500)
        safe_new = truncate_for_llm(new_text, max_chars=3500)
        messages = [
            {"role": "system", "content": DOCUMENT_COMPARISON_PROMPT},
            {
                "role": "user",
                "content": f"OLD DOCUMENT:\n{safe_old}\n\nNEW DOCUMENT:\n{safe_new}",
            },
        ]
        try:
            content = self._execute_completion(messages, temperature=0, json_mode=True)
            parsed = json.loads(content or "{}")
            if not isinstance(parsed, dict):
                parsed = {}
            return self._normalize_comparison_result(
                parsed,
                default_summary="Document comparison complete.",
            )
        except Exception as exc:
            logger.warning("Document comparison LLM error or fallback: %s", exc)
            return self._normalize_comparison_result(
                {},
                default_summary="Comparison could not be completed automatically.",
            )

    def synthesize_case(
        self,
        case_title: str,
        combined_text: str,
    ) -> dict:
        safe_text = truncate_for_llm(combined_text, max_chars=6000)
        messages = [
            {"role": "system", "content": CASE_SYNTHESIS_PROMPT},
            {
                "role": "user",
                "content": f"CASE TITLE: {case_title}\n\nMATTER DOCUMENTS CONTENT:\n{safe_text}",
            },
        ]
        content = self._execute_completion(messages, temperature=0, json_mode=True)
        try:
            return json.loads(content or "{}")
        except json.JSONDecodeError:
            return {
                "overall_risk_score": 50,
                "overall_risk_level": "Medium",
                "executive_summary": f"Matter analysis generated for '{case_title}'.",
                "key_issues": [],
                "recommended_actions": [],
            }


openai_service = OpenAIService()
