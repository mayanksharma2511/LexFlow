from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums.case_priority import CasePriority
from app.enums.case_status import CaseStatus


def normalize_priority(v: Any) -> CasePriority:
    if isinstance(v, CasePriority):
        return v
    s = str(v or "").upper()
    if "HIGH" in s:
        return CasePriority.HIGH
    if "LOW" in s:
        return CasePriority.LOW
    return CasePriority.MEDIUM


def normalize_status(v: Any) -> CaseStatus:
    if isinstance(v, CaseStatus):
        return v
    s = str(v or "").upper()
    if "PROGRESS" in s:
        return CaseStatus.IN_PROGRESS
    if "CLOSE" in s:
        return CaseStatus.CLOSED
    return CaseStatus.OPEN


class CaseCreate(BaseModel):
    title: str = Field(
        ...,
        min_length=3,
        max_length=255,
    )

    case_number: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    client_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    opposing_party: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    court: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    description: str = Field(
        ...,
        min_length=1,
    )

    priority: CasePriority | str | None = CasePriority.MEDIUM

    @field_validator("priority", mode="before")
    @classmethod
    def validate_create_priority(cls, v: Any) -> CasePriority:
        return normalize_priority(v)


class CaseUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=255,
    )

    client_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    opposing_party: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    court: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        min_length=1,
    )

    status: CaseStatus | None = None
    priority: CasePriority | None = None

    @field_validator("priority", mode="before")
    @classmethod
    def validate_update_priority(cls, v: Any) -> CasePriority | None:
        return normalize_priority(v) if v is not None else None

    @field_validator("status", mode="before")
    @classmethod
    def validate_update_status(cls, v: Any) -> CaseStatus | None:
        return normalize_status(v) if v is not None else None


class CaseResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: str
    title: str
    case_number: str
    client_name: str
    opposing_party: str
    court: str
    description: str
    status: CaseStatus
    priority: CasePriority
    owner_id: str

    @field_validator("priority", mode="before")
    @classmethod
    def validate_priority(cls, v: Any) -> CasePriority:
        return normalize_priority(v)

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v: Any) -> CaseStatus:
        return normalize_status(v)


class CaseDashboardDocument(BaseModel):
    id: str
    file_name: str
    document_type: str
    version: int = 1
    uploaded_at: datetime
    analysis_count: int


class CaseDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    case_number: str
    client_name: str
    opposing_party: str
    court: str
    description: str
    status: CaseStatus
    priority: CasePriority
    documents: list[CaseDashboardDocument]
    document_count: int

    @field_validator("priority", mode="before")
    @classmethod
    def validate_priority(cls, v: Any) -> CasePriority:
        return normalize_priority(v)

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v: Any) -> CaseStatus:
        return normalize_status(v)


class CaseStatsSummary(BaseModel):
    active_cases: int
    total_documents: int
    total_ai_analyses: int
    pending_review: int
