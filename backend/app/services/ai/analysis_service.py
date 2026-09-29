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
from app.services.ai.llm_service import llm_service
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


def generate_fallback_clauses(extracted_text: str | None) -> dict:
    """Pull out only what simple patterns can find (parties, dates, governing law) when the
    AI service is unavailable. Anything not found is left out rather than filled in."""
    text = extracted_text or ""
    data: dict[str, Any] = {}

    parties: list[str] = []
    # "between X and Y" (the usual opening of a contract): take both sides
    pair = re.search(
        r"(?:by and between|between)\s+([A-Z][^\n]{2,80}?)\s+and\s+([A-Z][^\n]{2,80}?)"
        r"(?=\s*(?:[\.,;(\n]|$|\b(?:dated|as of|effective|whereby|each)\b))",
        text,
    )
    if pair:
        parties = [p.strip(" ,") for p in pair.groups() if 2 < len(p.strip(" ,")) < 100]
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

        texts = []
        for doc in documents:
            if doc.extracted_text and doc.extracted_text.strip():
                texts.append(f"--- DOCUMENT: {doc.file_name} ---\n{doc.extracted_text[:4000]}")

        combined_text = "\n\n".join(texts)
        if not combined_text.strip():
            return {
                "overall_risk_score": None,
                "overall_risk_level": "Not available",
                "executive_summary": "No readable text extracted from case documents.",
                "key_issues": [],
                "recommended_actions": ["Re-upload documents with readable text or OCR coverage."],
            }

        try:
            raw_res = llm_service.synthesize_case(case.title, combined_text)
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
