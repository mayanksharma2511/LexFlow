"""Tests for keyword search across case documents."""

from app.services.ai.search_service import KeywordSearchService, Passage


def _passages(service: KeywordSearchService, text: str) -> list[Passage]:
    return [
        Passage(passage_id=f"p_{i}", document_id="doc_1", file_name="lease.pdf", passage_index=i, text=t)
        for i, t in enumerate(service.split_into_passages(text, size=100, overlap=20))
    ]


def test_passages_overlap_and_cover_text() -> None:
    service = KeywordSearchService()
    text = (
        "This Lease Agreement governs the rental of commercial space in San Francisco. "
        "The Tenant shall maintain liability insurance of $1,000,000 during the term. "
        "Any disputes shall be resolved through arbitration in California."
    )
    parts = service.split_into_passages(text, size=100, overlap=20)
    assert len(parts) >= 2
    assert "arbitration" in parts[-1]


def test_search_ranks_the_matching_passage_first() -> None:
    service = KeywordSearchService()
    text = (
        "This Lease Agreement governs the rental of commercial space in San Francisco. "
        "The Tenant shall maintain liability insurance of $1,000,000 during the term. "
        "Any disputes shall be resolved through arbitration in California."
    )
    results = service.search("liability insurance", _passages(service, text), top_k=2)
    assert results
    assert "insurance" in results[0].text_snippet
    assert 0.0 < results[0].relevance_score <= 1.0


def test_search_returns_nothing_without_shared_words() -> None:
    service = KeywordSearchService()
    passages = _passages(service, "The Tenant shall pay rent monthly.")
    assert service.search("spaceship propulsion", passages) == []
