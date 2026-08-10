from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.enums.document_type import DocumentType
from app.models.user import User
from app.schemas.document import (
    DocumentAnalysisSummary,
    DocumentCreate,
    DocumentDetailsResponse,
    DocumentResponse,
)
from app.services.ai.analysis_service import ai_analysis_service
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
    current_user: User = Depends(get_current_user),
):

    return document_service.get_user_documents(
        db,
        current_user.id,
    )


@router.get(
    "/{document_id}/download",
)
def download_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    document = document_service.get_user_document(
        db,
        document_id,
        current_user.id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    filepath = Path(document.file_path)

    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found.",
        )

    return FileResponse(
        path=str(filepath),
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
    current_user: User = Depends(get_current_user),
):

    document = DocumentCreate(
        case_id=case_id,
        document_type=document_type,
    )

    try:
        return document_service.upload_document(
            db=db,
            file=file,
            data=document,
            user_id=current_user.id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:
        document_service.delete_document(
            db,
            document_id,
            current_user.id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

@router.get(
    "/{document_id}",
    response_model=DocumentDetailsResponse,
)
def get_document_details(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    document = document_service.get_user_document(
        db,
        document_id,
        current_user.id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    analyses = ai_analysis_service.get_document_analyses(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
    )

    return DocumentDetailsResponse(
        id=document.id,
        file_name=document.file_name,
        document_type=document.document_type,
        case_id=document.case_id,
        extracted_text=document.extracted_text,
        analyses=[
            DocumentAnalysisSummary(
                analysis_type=analysis.analysis_type,
                result=analysis.result,
                created_at=analysis.created_at,
            )
            for analysis in analyses
        ],
    )
