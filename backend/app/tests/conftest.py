"""Test settings shared by all tests."""

import pytest

from app.core.config import settings


@pytest.fixture(autouse=True)
def no_real_ai_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests must never call the real AI service (or spend its free-tier quota),
    even if backend/.env contains a GROQ_API_KEY."""
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")


@pytest.fixture(autouse=True)
def no_saved_classifier(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests do not depend on a locally trained clause classifier; tests that need one supply it."""
    from app.services.ai import clause_classifier

    monkeypatch.setattr(clause_classifier, "load_model", lambda: None)
