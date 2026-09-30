"""The trained clause classifier used when the AI is unavailable (a tiny model stands in for it)."""

import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from app.services.ai import clause_classifier
from app.services.ai.analysis_service import generate_fallback_clauses
from app.services.ai.clause_classifier import passages
from app.services.ai.prompts import CLAUSE_TYPES

LAW = "This Agreement shall be governed by the laws of the State of New York."
TEXT = (
    "SUPPLY AGREEMENT between Acme Corp and Beta LLC.\n\n1. Deliveries.\n\n"
    "The Supplier will deliver the goods every week to the Buyer's warehouse. " + LAW +
    " Invoices are payable within thirty days of receipt."
)


def test_passages_cover_sentences_and_attach_short_headings() -> None:
    texts = [TEXT[s:e] for s, e in passages(TEXT)]
    assert LAW in texts
    assert any(t.startswith("1. Deliveries.") for t in texts)  # the heading joins the next sentence


@pytest.fixture
def tiny_model(monkeypatch: pytest.MonkeyPatch) -> None:
    train = [LAW, "Governed by the laws of Delaware.", "Deliveries are made weekly.", "Invoices are paid monthly."]
    vectorizer = TfidfVectorizer().fit(train)
    law_model = LogisticRegression().fit(vectorizer.transform(train), [1, 1, 0, 0])
    types = list(CLAUSE_TYPES)
    bundle = {
        "vectorizer": vectorizer,
        "models": [law_model if t == "Governing Law" else None for t in types],
        "settings": {t: (0.5, 1) for t in types},
        "types": types,
    }
    monkeypatch.setattr(clause_classifier, "load_model", lambda: bundle)


def test_fallback_uses_the_classifier_and_checks_its_quotes(tiny_model) -> None:  # noqa: ANN001
    result = generate_fallback_clauses(TEXT)
    assert result["method"] == "trained classifier"
    assert result["confidence"] is None
    (clause,) = result["data"]["clauses"]
    assert clause["type"] == "Governing Law"
    assert clause["quote"] == LAW
    assert clause["verification"] == "exact"
    assert result["data"]["parties"] == ["Acme Corp", "Beta LLC"]


def test_without_a_trained_model_the_fallback_uses_text_patterns() -> None:
    assert generate_fallback_clauses(TEXT)["method"] == "text patterns"
