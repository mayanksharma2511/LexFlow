"""API endpoint for Hybrid NLP summarization combining TF-IDF and LLM abstractions."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.ai.hybrid_nlp import HybridSummaryResult, hybrid_nlp_service
from app.services.document import document_service

router = APIRouter(
    prefix="/ai",
    tags=["AI Hybrid NLP"],
)


@router.post(
    "/documents/{document_id}/hybrid-summary",
    response_model=HybridSummaryResult,
)
def generate_hybrid_summary(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HybridSummaryResult:
    """Generate a hybrid TF-IDF extractive and LLM abstractive document summary.

    Args:
        document_id: Unique target document identifier.
        db: Database session instance.
        current_user: Authenticated User model instance.

    Returns:
        HybridSummaryResult instance.
    """
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

    text = document.extracted_text or ""
    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no extracted text content for hybrid summarization.",
        )

    return hybrid_nlp_service.summarize_hybrid(text)
