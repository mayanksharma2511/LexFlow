from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    summary: str


class ClauseExtractionResponse(BaseModel):
    document_type: str
    confidence: float | None = None  # the AI's own estimate; None when rules were used instead
    method: str | None = None
    note: str | None = None
    data: dict[str, Any]


class ClassificationResponse(BaseModel):
    document_type: str
    confidence: float | None = None  # the AI's own estimate; None when rules were used instead
    method: str | None = None
    note: str | None = None


class Risk(BaseModel):
    title: str
    severity: str
    description: str
    quote: str | None = None
    verification: str | None = None  # "exact", "close" or "not_found" (see grounding.py)
    match_score: float | None = None


class RiskAnalysisResponse(BaseModel):
    risk_score: int | None = None  # None when the analysis could not be run
    risk_level: str
    risks: list[Risk]
    note: str | None = None
    coverage: dict[str, int] | None = None


class ComparisonChange(BaseModel):
    old: str
    new: str


class ComparisonResponse(BaseModel):
    summary: str
    added: list[ComparisonChange]
    removed: list[ComparisonChange]
    modified: list[ComparisonChange]

class AnalysisHistoryResponse(BaseModel):
    id: str
    document_id: str
    analysis_type: str
    result: str
    created_at: datetime

class LatestAnalysisResponse(BaseModel):
    id: str
    document_id: str
    analysis_type: str
    result: str
    created_at: datetime

class AIAnalysisResponse(BaseModel):

    id: str

    document_id: str

    analysis_type: str

    result: str

    created_at: datetime
