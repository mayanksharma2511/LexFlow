from pydantic import BaseModel, ConfigDict, Field

from app.enums.case_priority import CasePriority
from app.enums.case_status import CaseStatus


class CaseCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    case_number: str
    client_name: str
    opposing_party: str
    court: str
    description: str


class CaseUpdate(BaseModel):
    title: str | None = None
    client_name: str | None = None
    opposing_party: str | None = None
    court: str | None = None
    description: str | None = None
    status: CaseStatus | None = None
    priority: CasePriority | None = None


class CaseResponse(BaseModel):
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
    owner_id: str