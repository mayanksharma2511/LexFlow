from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    summary: str


class ClauseExtractionResponse(BaseModel):
    document_type: str
    confidence: float
    data: dict[str, Any]


class ClassificationResponse(BaseModel):
    document_type: str
    confidence: float


class Risk(BaseModel):
    title: str
    severity: str
    description: str


class RiskAnalysisResponse(BaseModel):
    risk_score: int
    risk_level: str
    risks: list[Risk]


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
