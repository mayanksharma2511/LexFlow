from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
)
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from fastapi import HTTPException, status
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

@router.get(
    "/{document_id}/download",
)
def download_document(
    document_id: str,
    db: Session = Depends(get_db),
):

    document = document_service.get_document(
        db,
        document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return FileResponse(
        path=document.file_path,
        filename=document.file_name,
    )

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

@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    try:
        document_service.delete_document(
            db,
            document_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )