from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.enums.document_type import DocumentType
from app.schemas.document import (
    DocumentCreate,
    DocumentResponse,
)
from app.services.document import document_service

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.get(
    "",
    response_model=list[DocumentResponse],
)
def get_documents(
    db: Session = Depends(get_db),
):
    return document_service.get_all_documents(db)

@router.post(
    "/upload",
    response_model=DocumentResponse,
)
def upload_document(
    case_id: str = Form(...),
    document_type: DocumentType = Form(DocumentType.OTHER),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    document = DocumentCreate(
        case_id=case_id,
        document_type=document_type,
    )

    return document_service.upload_document(
        db=db,
        file=file,
        data=document,
    )