from app.schemas.ai import ComparisonResponse
from app.services.ai.openai_service import openai_service


def test_comparison_result_normalization_successful():
    raw_data = {
        "summary": "Rent changed.",
        "added": [{"old": "", "new": "Clause A"}],
        "removed": [],
        "modified": [{"old": "$2000", "new": "$2500"}],
    }
    normalized = openai_service._normalize_comparison_result(raw_data)
    validated = ComparisonResponse(**normalized)
    assert validated.summary == "Rent changed."
    assert len(validated.added) == 1
    assert validated.added[0].new == "Clause A"
    assert len(validated.modified) == 1
    assert validated.modified[0].old == "$2000"


def test_comparison_result_normalization_missing_categories():
    # Model returns only summary
    raw_data = {"summary": "No major changes identified."}
    normalized = openai_service._normalize_comparison_result(raw_data)
    validated = ComparisonResponse(**normalized)
    assert validated.summary == "No major changes identified."
    assert validated.added == []
    assert validated.removed == []
    assert validated.modified == []


def test_comparison_result_normalization_alternative_differences_key():
    # Model returns legacy 'differences' key instead of added/removed/modified
    raw_data = {
        "summary": "Differences detected.",
        "differences": [{"old": "Term 1", "new": "Term 2"}],
    }
    normalized = openai_service._normalize_comparison_result(raw_data)
    validated = ComparisonResponse(**normalized)
    assert validated.summary == "Differences detected."
    assert len(validated.modified) == 1
    assert validated.modified[0].old == "Term 1"


def test_comparison_fallback_on_empty_dict():
    normalized = openai_service._normalize_comparison_result({})
    validated = ComparisonResponse(**normalized)
    assert validated.summary == "Document comparison complete."
    assert validated.added == []
    assert validated.removed == []
    assert validated.modified == []
