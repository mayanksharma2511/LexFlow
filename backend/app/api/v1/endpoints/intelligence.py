"""Keyword search across the documents in a case."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.case import case_repository
from app.repositories.document import document_repository
from app.services.ai.search_service import Passage, SearchResult, search_service

router = APIRouter(
    prefix="/cases",
    tags=["Search"],
)


@router.get(
    "/{case_id}/search",
    response_model=list[SearchResult],
)
def search_case_documents(
    case_id: str,
    query: str = Query(..., min_length=1, description="Words to search for"),
    top_k: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SearchResult]:
    """Rank passages from the case's documents by keyword relevance to the query.
    Only the owner of the case can search it."""
    case = case_repository.get_by_id_and_owner(db, case_id, current_user.id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

    passages: list[Passage] = []
    for doc in document_repository.get_by_case(db, case_id):
        if not doc.extracted_text:
            continue
        for idx, text in enumerate(search_service.split_into_passages(doc.extracted_text)):
            passages.append(Passage(
                passage_id=f"{doc.id}_p{idx}",
                document_id=doc.id,
                file_name=doc.file_name,
                passage_index=idx,
                text=text,
            ))

    return search_service.search(query=query, passages=passages, top_k=top_k)
