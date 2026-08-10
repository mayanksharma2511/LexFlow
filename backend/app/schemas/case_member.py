from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CaseMemberCreate(BaseModel):
    user_id: str = Field(..., min_length=1)
    role_in_case: str = Field(default="Co-Counsel", min_length=1, max_length=50)


class CaseMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    user_id: str
    role_in_case: str
    full_name: str | None = None
    email: str | None = None
    created_at: datetime
