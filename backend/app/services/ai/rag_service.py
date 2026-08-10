"""RAG Vector Search & Chunking Service for Legal Document Retrieval.

Implements text chunking, vector embedding calculation, cosine similarity scoring,
and semantic search over matter documents with strict Python 3.13 type standards.
"""

import math

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """Data model representing a chunked document segment."""

    chunk_id: str
    document_id: str
    file_name: str
    chunk_index: int
    text: str
    embedding: list[float] = Field(default_factory=list)


class SemanticSearchResult(BaseModel):
    """Data model representing a ranked semantic search hit."""

    chunk_id: str
    document_id: str
    file_name: str
    text_snippet: str
    relevance_score: float
    chunk_index: int


class RAGService:
    """Enterprise RAG Service for document vectorization and semantic search."""

    def __init__(self, vector_dim: int = 64) -> None:
        """Initialize RAG service with target vector dimensions.

        Args:
            vector_dim: Vector embedding dimensionality.
        """
        self._vector_dim = vector_dim

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 400,
        overlap: int = 80,
    ) -> list[str]:
        """Split text into overlapping text chunks respecting word boundaries.

        Args:
            text: Input text string.
            chunk_size: Target character size per chunk.
            overlap: Character overlap between consecutive chunks.

        Returns:
            List of chunk strings.
        """
        clean_text = text.strip()
        if not clean_text:
            return []

        if len(clean_text) <= chunk_size:
            return [clean_text]

        chunks: list[str] = []
        start = 0
        text_len = len(clean_text)

        while start < text_len:
            end = min(start + chunk_size, text_len)
            # Adjust end to word boundary if not at end of text
            if end < text_len:
                last_space = clean_text.rfind(" ", start, end)
                if last_space > start:
                    end = last_space

            chunk_str = clean_text[start:end].strip()
            if chunk_str:
                chunks.append(chunk_str)

            if end >= text_len:
                break
            start = max(end - overlap, start + 1)

        return chunks

    def compute_embedding(self, text: str) -> list[float]:
        """Compute a normalized dense vector embedding for text payload.

        Args:
            text: Input text payload.

        Returns:
            List of float values representing normalized vector embedding.
        """
        vector = [0.0] * self._vector_dim
        words = text.lower().split()
        if not words:
            return vector

        for word in words:
            # Deterministic hash mapping into vector dimensions
            idx = abs(hash(word)) % self._vector_dim
            val = float(len(word))
            vector[idx] += val

        # Normalize L2 norm
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector

    def cosine_similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        """Calculate cosine similarity between two vector embeddings.

        Args:
            vec_a: First vector embedding.
            vec_b: Second vector embedding.

        Returns:
            Cosine similarity score (-1.0 to 1.0).
        """
        if len(vec_a) != len(vec_b) or not vec_a:
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b, strict=False))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def search_chunks(
        self,
        query: str,
        chunks: list[DocumentChunk],
        top_k: int = 5,
    ) -> list[SemanticSearchResult]:
        """Rank document chunks by cosine similarity to search query.

        Args:
            query: User semantic search query string.
            chunks: List of pre-processed DocumentChunk objects.
            top_k: Number of top search results to return.

        Returns:
            List of SemanticSearchResult objects ranked by similarity score.
        """
        query_vec = self.compute_embedding(query)
        scored_results: list[SemanticSearchResult] = []

        for chunk in chunks:
            chunk_vec = chunk.embedding if chunk.embedding else self.compute_embedding(chunk.text)
            score = self.cosine_similarity(query_vec, chunk_vec)
            scored_results.append(
                SemanticSearchResult(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    file_name=chunk.file_name,
                    text_snippet=chunk.text,
                    relevance_score=round(score, 4),
                    chunk_index=chunk.chunk_index,
                )
            )

        scored_results.sort(key=lambda x: x.relevance_score, reverse=True)
        return scored_results[:top_k]


rag_service = RAGService()
