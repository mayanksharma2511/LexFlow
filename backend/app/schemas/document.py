from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums.document_type import DocumentType


class DocumentCreate(BaseModel):
    case_id: str
    document_type: DocumentType = DocumentType.OTHER


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_name: str
    document_type: DocumentType
    case_id: str
    version: int = 1
    extracted_text: str | None
    status: str | None = "COMPLETED"
    error_message: str | None = None
    uploaded_at: datetime | None = None

class DocumentAnalysisSummary(BaseModel):
    analysis_type: str
    result: str
    created_at: datetime


class DocumentDetailsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_name: str
    document_type: DocumentType
    case_id: str
    version: int = 1
    extracted_text: str | None
    status: str | None = "COMPLETED"
    error_message: str | None = None
    uploaded_at: datetime | None = None
    analyses: list[DocumentAnalysisSummary]
