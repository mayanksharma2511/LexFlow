"""Unit tests for Hybrid NLP TF-IDF extractive summarizer."""

from app.services.ai.hybrid_nlp import HybridNLPService, HybridSummaryResult


def test_hybrid_nlp_tfidf_extraction() -> None:
    """Test TF-IDF sentence extraction scoring and ranking logic."""
    service = HybridNLPService()
    text = (
        "The Lessee agrees to pay rent of $5000 per month on the first day of each month. "
        "Failure to make timely payment shall incur a late fee of 5 percent. "
        "The Lessor reserves the right to inspect the leased premises upon 24 hours notice. "
        "Governing law shall be the State of California with exclusive venue in San Francisco. "
        "This agreement constitutes the entire understanding between the parties."
    )

    extracted = service.extract_key_sentences(text, top_n=3)
    assert len(extracted) == 3
    assert all(item.score > 0 for item in extracted)
    # Check original index ordering
    indices = [item.original_index for item in extracted]
    assert indices == sorted(indices)


def test_hybrid_nlp_summarize_hybrid_structure() -> None:
    """Test full hybrid NLP summary payload generation."""
    service = HybridNLPService()
    text = (
        "Contractual obligations mandate strict compliance with environmental regulations. "
        "Any non-compliance will result in immediate termination and financial indemnity. "
        "Parties agree to attempt good-faith mediation prior to formal arbitration."
    )

    result: HybridSummaryResult = service.summarize_hybrid(text)
    assert result.original_char_count == len(text)
    assert len(result.extractive_sentences) > 0
    assert result.abstractive_summary is not None
    assert 0.0 <= result.compression_ratio <= 1.0
