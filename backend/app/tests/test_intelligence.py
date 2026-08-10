"""Unit tests for Knowledge Graph Service and RAG Vector Search."""

from app.services.ai.knowledge_graph import KnowledgeGraphService, NodeType
from app.services.ai.rag_service import DocumentChunk, RAGService


def test_knowledge_graph_entity_extraction() -> None:
    """Test knowledge graph node and edge extraction logic."""
    service = KnowledgeGraphService()
    text = (
        "The Lessor and Lessee agree to California jurisdiction. "
        "Monthly rent is $12,500 due on the first of each month."
    )

    result = service.extract_entities_and_build_graph(text, case_id="case_101")
    assert result.case_id == "case_101"
    assert len(result.nodes) > 1

    node_types = {n.node_type for n in result.nodes}
    assert NodeType.PARTY in node_types
    assert NodeType.JURISDICTION in node_types
    assert NodeType.VALUATION in node_types
    assert len(result.gnn_adjacency_matrix) == len(result.nodes)


def test_rag_chunking_and_embedding() -> None:
    """Test RAG document chunking, embedding generation, and cosine search."""
    service = RAGService(vector_dim=32)
    sample_text = (
        "This Lease Agreement governs the rental of commercial space in San Francisco. "
        "The Tenant shall maintain liability insurance of $1,000,000 during the term. "
        "Any disputes shall be resolved through arbitration in California."
    )

    chunks = service.chunk_text(sample_text, chunk_size=100, overlap=20)
    assert len(chunks) >= 2

    doc_chunks = [
        DocumentChunk(
            chunk_id=f"c_{i}",
            document_id="doc_1",
            file_name="lease.pdf",
            chunk_index=i,
            text=c,
            embedding=service.compute_embedding(c),
        )
        for i, c in enumerate(chunks)
    ]

    results = service.search_chunks("liability insurance", doc_chunks, top_k=2)
    assert len(results) > 0
    assert results[0].relevance_score >= 0.0
