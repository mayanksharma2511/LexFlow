from pydantic import BaseModel, ConfigDict, Field

from app.enums.document_type import DocumentType


class DocumentCreate(BaseModel):
    case_id: str
    document_type: DocumentType = DocumentType.OTHER


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_name: str
    file_path: str
    document_type: DocumentType
    case_id: str
    extracted_text: str | None