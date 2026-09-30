"""Test settings shared by all tests."""

import pytest

from app.core.config import settings


@pytest.fixture(autouse=True)
def no_real_ai_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests must never call the real AI service (or spend its free-tier quota),
    even if backend/.env contains a GROQ_API_KEY."""
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
