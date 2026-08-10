"""API Endpoints for Advanced Intelligence (Knowledge Graph & RAG Semantic Search)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.case import case_repository
from app.repositories.document import document_repository
from app.services.ai.knowledge_graph import (
    KnowledgeGraphResult,
    knowledge_graph_service,
)
from app.services.ai.rag_service import DocumentChunk, SemanticSearchResult, rag_service

router = APIRouter(
    prefix="/cases",
    tags=["Advanced Intelligence"],
)


@router.get(
    "/{case_id}/semantic-search",
    response_model=list[SemanticSearchResult],
)
def semantic_search_case_documents(
    case_id: str,
    query: str = Query(..., min_length=1, description="Search query string"),
    top_k: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SemanticSearchResult]:
    """Execute RAG vector semantic search over all documents in a legal matter.

    Args:
        case_id: Target case ID.
        query: Search query text.
        top_k: Max results to return.
        db: Database session instance.
        current_user: Authenticated User model instance.

    Returns:
        List of ranked SemanticSearchResult objects.
    """
    case = case_repository.get_by_id(db, case_id)
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found.",
        )

    documents = document_repository.get_by_case(db, case_id)
    if not documents:
        return []

    all_chunks: list[DocumentChunk] = []
    for doc in documents:
        if not doc.extracted_text:
            continue

        raw_chunks = rag_service.chunk_text(doc.extracted_text)
        for idx, chunk_str in enumerate(raw_chunks):
            embedding = rag_service.compute_embedding(chunk_str)
            all_chunks.append(
                DocumentChunk(
                    chunk_id=f"{doc.id}_c{idx}",
                    document_id=doc.id,
                    file_name=doc.file_name,
                    chunk_index=idx,
                    text=chunk_str,
                    embedding=embedding,
                )
            )

    return rag_service.search_chunks(query=query, chunks=all_chunks, top_k=top_k)


@router.get(
    "/{case_id}/knowledge-graph",
    response_model=KnowledgeGraphResult,
)
def get_case_knowledge_graph(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeGraphResult:
    """Generate a GNN-compatible Knowledge Graph for a legal matter.

    Args:
        case_id: Target case ID.
        db: Database session instance.
        current_user: Authenticated User model instance.

    Returns:
        KnowledgeGraphResult instance.
    """
    case = case_repository.get_by_id(db, case_id)
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found.",
        )

    documents = document_repository.get_by_case(db, case_id)
    combined_texts = [d.extracted_text for d in documents if d.extracted_text]
    full_text = "\n\n".join(combined_texts) if combined_texts else case.description or case.title

    return knowledge_graph_service.extract_entities_and_build_graph(
        text=full_text,
        case_id=case_id,
    )
