from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.document import document_repository
from app.schemas.ai import SummaryResponse
from app.services.ai.openai_service import openai_service

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post(
    "/documents/{document_id}/summary",
    response_model=SummaryResponse,
)
def summarize_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    document = document_repository.get_by_id(
        db,
        document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    summary = openai_service.summarize(
        document.extracted_text,
    )

    return SummaryResponse(
        summary=summary,
    )