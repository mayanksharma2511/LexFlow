from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AIAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    analysis_type: str
    result: str
    created_at: datetime
