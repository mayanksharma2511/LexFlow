import json
import logging
import re
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import LLMServiceError
from app.models.ai_analysis import AIAnalysis
from app.models.document import Document
from app.repositories.ai_analysis import ai_analysis_repository
from app.repositories.case import case_repository
from app.repositories.document import document_repository
from app.services.ai.clause_classifier import find_clauses
from app.services.ai.grounding import normalize_with_offsets, verify_quote
from app.services.ai.llm_service import _verify_items, llm_service, split_into_sections
from app.services.ai.prompts import CLAUSE_TYPES
from app.services.audit_log import audit_log_service

logger = logging.getLogger(__name__)


AI_UNAVAILABLE_NOTE = (
    "The AI service was unavailable, so this result comes from simple text rules "
    "applied to the document, not from the AI model."
)


def generate_fallback_summary(file_name: str, extracted_text: str | None) -> str:
    """When the AI service is unavailable, show the document's opening lines instead of a summary.

    Nothing here is generated: it is the document's own text, labelled as such.
    """
    if not extracted_text or not extracted_text.strip():
        return (
            f"AI summary unavailable for '{file_name}', and no text could be extracted from the document."
        )

    lines = [line.strip() for line in extracted_text.splitlines() if line.strip()]
    opening = "\n".join(lines[:6])
    return (
        f"### AI summary unavailable ({file_name})\n"
        "The AI service could not be reached, so no summary was generated. "
        f"The document has {len(extracted_text.split())} words. Its opening lines are:\n\n{opening}"
    )


def generate_fallback_classification(extracted_text: str | None) -> dict:
    """Guess the document type from keywords when the AI service is unavailable.

    No confidence is given, because keyword rules do not produce a measured confidence.
    """
    text_upper = (extracted_text or "").upper()
    doc_type = "Unknown"
    if "PETITION" in text_upper or "PLAINT" in text_upper:
        doc_type = "Petition"
    elif "LEASE" in text_upper or "TENANT" in text_upper:
        doc_type = "Lease Agreement"
    elif "NON-DISCLOSURE" in text_upper or "CONFIDENTIALITY AGREEMENT" in text_upper:
        doc_type = "NDA"
    elif "EMPLOYMENT" in text_upper and "AGREEMENT" in text_upper:
        doc_type = "Employment Contract"
    elif "AFFIDAVIT" in text_upper or "SWORN" in text_upper:
        doc_type = "Affidavit"
    elif "AGREEMENT" in text_upper or "CONTRACT" in text_upper:
        doc_type = "Contract"

    return {
        "document_type": doc_type,
        "confidence": None,
        "method": "keyword rules",
        "note": AI_UNAVAILABLE_NOTE,
    }


CLASSIFIER_NOTE = (
    "The AI service was unavailable, so these clauses were found by LexFlow's own classifier, "
    "trained on contracts labelled by lawyers (CUAD). It finds passages but does not explain them."
)


def generate_fallback_clauses(extracted_text: str | None) -> dict:
    """Clauses found without the AI service: by the trained classifier when it is available,
    otherwise by simple text patterns. Anything not found is left out rather than filled in."""
    text = extracted_text or ""
    found = find_clauses(text) if text.strip() else None
    if found is not None:
        clauses = [
            {"type": f["type"], "quote": f["quote"],
             "explanation": "Found by LexFlow's trained classifier (no AI explanation available)."}
            for f in found
        ]
        sections = split_into_sections(text)
        return {
            "document_type": "Unknown",
            "confidence": None,
            "method": "trained classifier",
            "note": CLASSIFIER_NOTE,
            "data": {
                "parties": _parties(text),
                "clauses": [{**c, "source": "classifier"} for c in _verify_items(clauses, text)],
                "coverage": {"characters": len(text), "characters_read": len(text),
                             "sections": len(sections), "sections_read": len(sections)},
            },
        }
    return _pattern_clauses(text)


def _parties(text: str) -> list[str]:
    """The two sides of "between X and Y", the usual opening of a contract."""
    pair = re.search(
        r"(?:by and between|between)\s+([A-Z][^\n]{2,80}?)\s+and\s+([A-Z][^\n]{2,80}?)"
        r"(?=\s*(?:[\.,;(\n]|$|\b(?:dated|as of|effective|whereby|each)\b))",
        text,
    )
    if not pair:
        return []
    return [p.strip(" ,") for p in pair.groups() if 2 < len(p.strip(" ,")) < 100]


def _pattern_clauses(text: str) -> dict:
    """What simple patterns can find (parties, dates, governing law) when no classifier is available."""
    data: dict[str, Any] = {}

    parties = _parties(text)
    if parties:
        data["parties"] = parties

    dates = re.findall(
        r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+\d{1,2},\s+\d{4}|\d{1,2}\s+(?:January|February|March|"
        r"April|May|June|July|August|September|October|November|December)\s+\d{4})\b",
        text,
    )
    if dates:
        data["dates_found"] = list(dict.fromkeys(dates))[:5]

    law = re.search(r"governed by(?: and construed in accordance with)? the laws? of ([A-Z][A-Za-z\s]{2,40}?)[,\.;]", text)
    if law:
        data["governing_law"] = law.group(1).strip()

    return {
        "document_type": "Unknown",
        "confidence": None,
        "method": "text patterns",
        "note": AI_UNAVAILABLE_NOTE,
        "data": data,
    }


CLASSIFIER_ONLY_NOTE = "Found by LexFlow's trained classifier; the AI did not report this passage."


def _spans_overlap(a: tuple[int, int], b: tuple[int, int]) -> bool:
    """The same rule the evaluation uses: the overlap covers at least half of the shorter span."""
    overlap = min(a[1], b[1]) - max(a[0], b[0])
    shorter = min(a[1] - a[0], b[1] - b[0])
    return shorter > 0 and overlap >= 0.5 * shorter


def add_classifier_findings(text: str, result: dict) -> dict:
    """Combine the AI's clauses with the trained classifier's.

    On lawyer-labelled contracts the two found different clauses, and together they found more
    than either alone (see the README). Each clause is marked with where it came from:
    "ai", "classifier", or "both" when the classifier found the same passage as the AI.
    Without a trained classifier the AI's result is returned unchanged.
    """
    data = result.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("clauses"), list):
        return result
    found = find_clauses(text) if text.strip() else None
    if found is None:
        return result

    doc, _ = normalize_with_offsets(text)

    def span(quote: str) -> tuple[int, int] | None:
        check = verify_quote(quote, text, doc)
        return (check["start"], check["end"]) if check["start"] is not None else None

    clauses = [{**c, "source": "ai"} for c in data["clauses"]]
    ai_spans = [span(str(c.get("quote") or "")) for c in clauses]
    extra = []
    for f in found:
        f_span = span(f["quote"])
        matched = False
        for clause, a_span in zip(clauses, ai_spans):
            if clause.get("type") == f["type"] and a_span and f_span and _spans_overlap(a_span, f_span):
                clause["source"] = "both"
                matched = True
        if not matched:
            extra.append({"type": f["type"], "quote": f["quote"], "explanation": CLASSIFIER_ONLY_NOTE})
    clauses += [{**c, "source": "classifier"} for c in _verify_items(extra, text)]
    order = {t: i for i, t in enumerate(CLAUSE_TYPES)}
    clauses.sort(key=lambda c: order.get(str(c.get("type")), len(order)))
    return {**result, "data": {**data, "clauses": clauses, "combined_with_classifier": True}}


def unavailable_risk_result(reason: str) -> dict:
    """A risk analysis that could not be run. It must never look like a low-risk result."""
    return {
        "risk_score": None,
        "risk_level": "Not available",
        "risks": [],
        "note": f"Risk analysis could not be completed: {reason}",
    }


def _flatten_string_list(items: Any) -> list[str]:
    """Safely convert string/dict/list structures into a list of clean strings."""
    if not isinstance(items, list):
        if isinstance(items, str):
            return [items]
        if isinstance(items, dict):
            return [str(v) for v in items.values() if v]
        return []
    result: list[str] = []
    for item in items:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            vals = [str(v) for v in item.values() if v]
            result.append(" - ".join(vals) if vals else str(item))
        else:
            result.append(str(item))
    return result


class AIAnalysisService:

    def _get_document(
        self,
        db: Session,
        document_id: str,
        user_id: str,
    ) -> Document:
        document = document_repository.get_by_id_for_user(
            db,
            document_id,
            user_id,
        )

        if document is None:
            raise ValueError("Document not found.")

        return document

    def _handle_analysis_error(
        self,
        db: Session,
        document: Document,
        exc: Exception,
    ) -> None:
        """Mark document status as ANALYSIS_PAUSED or FAILED_QUOTA with readable error message."""
        status = "ANALYSIS_PAUSED" if isinstance(exc, LLMServiceError) else "FAILED_QUOTA"
        msg = str(exc) or "AI analysis paused due to service limit."
        document.status = status
        document.error_message = msg
        try:
            db.commit()
            db.refresh(document)
        except Exception:
            db.rollback()
        logger.warning("Document %s analysis updated to status=%s: %s", document.id, status, msg)

    def _save_analysis(
        self,
        db: Session,
        document_id: str,
        analysis_type: str,
        result: dict | str,
    ) -> AIAnalysis:

        if isinstance(result, dict):
            result_text = json.dumps(
                result,
                ensure_ascii=False,
            )
        else:
            result_text = result

        analysis = AIAnalysis(
            document_id=document_id,
            analysis_type=analysis_type,
            result=result_text,
        )

        return ai_analysis_repository.create(
            db,
            analysis,
        )

    def summarize(
        self,
        db: Session,
        document_id: str,
        user_id: str,
    ) -> str:

        document = self._get_document(
            db,
            document_id,
            user_id,
        )

        try:
            summary = llm_service.summarize(
                document.extracted_text or "",
            )
        except Exception as exc:
            self._handle_analysis_error(db, document, exc)
            summary = generate_fallback_summary(document.file_name, document.extracted_text)

        analysis = self._save_analysis(
            db,
            document_id,
            "summary",
            summary,
        )

        audit_log_service.log(
            db=db,
            user_id=user_id,
            action="AI_SUMMARY",
            entity_type="document",
            entity_id=document_id,
            details=f"AI summary generated for analysis '{analysis.id}'.",
        )

        return summary

    def classify(
        self,
        db: Session,
        document_id: str,
        user_id: str,
    ) -> dict:

        document = self._get_document(
            db,
            document_id,
            user_id,
        )

        try:
            result = llm_service.classify_document(
                document.extracted_text or "",
            )
        except Exception as exc:
            self._handle_analysis_error(db, document, exc)
            result = generate_fallback_classification(document.extracted_text)

        analysis = self._save_analysis(
            db,
            document_id,
            "classification",
            result,
        )

        audit_log_service.log(
            db=db,
            user_id=user_id,
            action="AI_CLASSIFICATION",
            entity_type="document",
            entity_id=document_id,
            details=f"AI classification generated for analysis '{analysis.id}'.",
        )

        return result

    def extract_clauses(
        self,
        db: Session,
        document_id: str,
        user_id: str,
    ) -> dict:

        document = self._get_document(
            db,
            document_id,
            user_id,
        )

        try:
            result = llm_service.extract_clauses(
                document.extracted_text or "",
            )
        except Exception as exc:
            self._handle_analysis_error(db, document, exc)
            result = generate_fallback_clauses(document.extracted_text)
        else:
            result = add_classifier_findings(document.extracted_text or "", result)

        analysis = self._save_analysis(
            db,
            document_id,
            "clause_extraction",
            result,
        )

        audit_log_service.log(
            db=db,
            user_id=user_id,
            action="AI_CLAUSE_EXTRACTION",
            entity_type="document",
            entity_id=document_id,
            details=f"AI clause extraction generated for analysis '{analysis.id}'.",
        )

        return result

    def analyze_risks(
        self,
        db: Session,
        document_id: str,
        user_id: str,
    ) -> dict:

        document = self._get_document(
            db,
            document_id,
            user_id,
        )

        try:
            result = llm_service.analyze_risks(
                document.extracted_text or "",
            )
        except Exception as exc:
            self._handle_analysis_error(db, document, exc)
            result = unavailable_risk_result(str(exc) or "the AI service was unavailable.")

        analysis = self._save_analysis(
            db,
            document_id,
            "risk_analysis",
            result,
        )

        audit_log_service.log(
            db=db,
            user_id=user_id,
            action="AI_RISK_ANALYSIS",
            entity_type="document",
            entity_id=document_id,
            details=f"AI risk analysis generated for analysis '{analysis.id}'.",
        )

        return result

    def compare_documents(
        self,
        db: Session,
        old_document_id: str,
        new_document_id: str,
        user_id: str,
    ) -> dict:

        old_document = self._get_document(
            db,
            old_document_id,
            user_id,
        )

        new_document = self._get_document(
            db,
            new_document_id,
            user_id,
        )

        try:
            result = llm_service.compare_documents(
                old_document.extracted_text or "",
                new_document.extracted_text or "",
            )
        except Exception as exc:
            self._handle_analysis_error(db, new_document, exc)
            result = {
                "summary": (
                    f"Comparison of '{old_document.file_name}' and '{new_document.file_name}' "
                    "could not be completed because the AI service was unavailable."
                ),
                "added": [],
                "removed": [],
                "modified": [],
            }

        analysis = self._save_analysis(
            db,
            new_document_id,
            "comparison",
            result,
        )

        audit_log_service.log(
            db=db,
            user_id=user_id,
            action="AI_DOCUMENT_COMPARISON",
            entity_type="document",
            entity_id=new_document_id,
            details=(
                f"Compared documents "
                f"'{old_document_id}' and '{new_document_id}' "
                f"for analysis '{analysis.id}'."
            ),
        )

        return result

    def get_document_analyses(
        self,
        db: Session,
        document_id: str,
        user_id: str,
    ) -> list[AIAnalysis]:

        self._get_document(
            db,
            document_id,
            user_id,
        )

        return ai_analysis_repository.get_all_by_document(
            db,
            document_id,
        )

    def get_latest_analysis(
        self,
        db: Session,
        document_id: str,
        analysis_type: str,
        user_id: str,
    ) -> AIAnalysis | None:

        self._get_document(
            db,
            document_id,
            user_id,
        )

        return ai_analysis_repository.get_by_document_and_type(
            db,
            document_id,
            analysis_type,
        )

    def synthesize_case_analysis(
        self,
        db: Session,
        case_id: str,
        user_id: str,
    ) -> dict:
        case = case_repository.get_by_id_and_owner(db, case_id, user_id)
        if case is None:
            raise ValueError("Case not found.")

        documents = document_repository.get_by_case(db, case_id)
        if not documents:
            return {
                "overall_risk_score": None,
                "overall_risk_level": "Not available",
                "executive_summary": "No documents found for this case.",
                "key_issues": [],
                "recommended_actions": ["Upload legal documents to initiate AI case synthesis."],
            }

        readable = [doc for doc in documents if doc.extracted_text and doc.extracted_text.strip()]
        if not readable:
            return {
                "overall_risk_score": None,
                "overall_risk_level": "Not available",
                "executive_summary": "No readable text extracted from case documents.",
                "key_issues": [],
                "recommended_actions": ["Re-upload documents with readable text or OCR coverage."],
            }

        try:
            # Work from each document's summary (reusing a saved one when it exists), so every
            # document is represented in full rather than by its first few thousand characters.
            summaries: list[tuple[str, str]] = []
            for doc in readable:
                saved = ai_analysis_repository.get_by_document_and_type(db, doc.id, "summary")
                if saved and saved.result and not saved.result.startswith("### AI summary unavailable"):
                    summaries.append((doc.file_name, saved.result))
                else:
                    summary = llm_service.summarize(doc.extracted_text or "")
                    self._save_analysis(db, doc.id, "summary", summary)
                    summaries.append((doc.file_name, summary))
            raw_res = llm_service.synthesize_case(case.title, summaries)
        except Exception as exc:
            logger.warning("Case synthesis degraded gracefully for case '%s': %s", case_id, exc)
            case.error_message = str(exc)
            try:
                db.commit()
            except Exception:
                db.rollback()
            raw_res = {
                "overall_risk_score": None,
                "overall_risk_level": "Not available",
                "executive_summary": (
                    f"AI synthesis for '{case.title}' could not be completed because the AI service "
                    "was unavailable. No issues or actions were generated."
                ),
                "key_issues": [],
                "recommended_actions": [],
            }

        raw_issues = raw_res.get("key_issues") or raw_res.get("issues") or []
        raw_actions = raw_res.get("recommended_actions") or raw_res.get("recommendations") or []

        normalized = {
            "overall_risk_score": raw_res.get("overall_risk_score"),
            "overall_risk_level": (
                str(raw_res["overall_risk_level"]).capitalize()
                if raw_res.get("overall_risk_level") else "Not available"
            ),
            "executive_summary": raw_res.get("executive_summary") or raw_res.get("summary") or f"Synthesized matter overview for {case.title}.",
            "key_issues": _flatten_string_list(raw_issues),
            "recommended_actions": _flatten_string_list(raw_actions),
        }

        audit_log_service.log(
            db=db,
            user_id=user_id,
            action="AI_CASE_SYNTHESIS",
            entity_type="case",
            entity_id=case_id,
            details=f"Generated case AI synthesis for case '{case.title}'.",
        )

        return normalized


ai_analysis_service = AIAnalysisService()
