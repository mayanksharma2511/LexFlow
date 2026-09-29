"""When the AI service fails, LexFlow must say so rather than show made-up results."""

import pytest

from app.core.exceptions import LLMServiceError
from app.services.ai.analysis_service import (
    generate_fallback_classification,
    generate_fallback_clauses,
    unavailable_risk_result,
)
from app.services.ai.llm_service import _parse_json


def test_failed_risk_analysis_is_not_reported_as_low_risk() -> None:
    result = unavailable_risk_result("timeout")
    assert result["risk_score"] is None
    assert result["risk_level"] == "Not available"
    assert result["risks"] == []


def test_rule_based_classification_has_no_made_up_confidence() -> None:
    result = generate_fallback_classification("THIS LEASE AGREEMENT is made between the Landlord and the Tenant.")
    assert result["document_type"] == "Lease Agreement"
    assert result["confidence"] is None
    assert result["method"] == "keyword rules"


def test_rule_based_clauses_only_report_what_is_in_the_text() -> None:
    text = (
        "This Agreement is made on March 3, 2021 by and between Acme Corp and Beta LLC. "
        "This Agreement shall be governed by the laws of Delaware."
    )
    data = generate_fallback_clauses(text)["data"]
    assert data["governing_law"] == "Delaware"
    assert "March 3, 2021" in data["dates_found"]
    assert data["parties"] == ["Acme Corp", "Beta LLC"]


def test_rule_based_clauses_leave_out_what_they_cannot_find() -> None:
    data = generate_fallback_clauses("A short note with no legal terms.")["data"]
    assert data == {}


def test_unreadable_ai_reply_is_an_error_not_a_default() -> None:
    with pytest.raises(LLMServiceError):
        _parse_json("not json", "risk analysis")
    assert _parse_json('{"risk_score": 40}', "risk analysis") == {"risk_score": 40}


def test_party_names_stop_before_trailing_words() -> None:
    text = "Distribution Agreement between EKR and PPI dated as of August 10, 2007 (the Original Agreement)."
    assert generate_fallback_clauses(text)["data"]["parties"] == ["EKR", "PPI"]
