"""LexFlow's own logic around the AI: reading whole documents, checking quotes, combining results.
The AI itself is replaced by a stand-in, so these tests need no API key."""

import json

import pytest

from app.services.ai import llm_service as module
from app.services.ai.llm_service import LLMService, split_into_sections

CONTRACT = (
    "SUPPLY AGREEMENT between Acme Corp and Beta LLC. "
    + "Filler text about deliveries and schedules. " * 400
    + "This Agreement shall be governed by the laws of the State of New York. "
    + "More filler about invoices and packaging. " * 400
    + "Neither party may assign this Agreement without the prior written consent of the other party."
)


def test_sections_cover_the_whole_document_with_overlap() -> None:
    sections = split_into_sections(CONTRACT, size=5000, overlap=300)
    assert len(sections) > 3
    assert sections[0][0] == 0
    last_start, last_text = sections[-1]
    assert last_start + len(last_text) == len(CONTRACT)
    for (s1, t1), (s2, _) in zip(sections, sections[1:]):
        assert s2 < s1 + len(t1)  # consecutive sections overlap, so nothing is skipped


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch) -> tuple[LLMService, list[str]]:
    """A service whose AI replies with one real quote and one invented one for every section."""
    calls: list[str] = []

    def fake_completion(self, messages, **kwargs):  # noqa: ANN001
        section = messages[-1]["content"]
        calls.append(section)
        if "classify" in messages[0]["content"]:
            return json.dumps({"document_type": "Purchase Agreement", "confidence": 0.9})
        clauses = [{"type": "Anti-Assignment", "quote": "Payments are due within ten days of receipt.", "explanation": "invented"}]
        if "laws of the State of New York" in section:
            clauses.append({"type": "Governing Law",
                            "quote": "This Agreement shall be governed by the laws of the State of New York.",
                            "explanation": "New York law applies."})
        return json.dumps({"parties": ["Acme Corp", "Beta LLC"], "clauses": clauses})

    monkeypatch.setattr(LLMService, "_execute_completion", fake_completion)
    monkeypatch.setattr(module.settings, "LLM_SECTION_CHARS", 5000)
    return LLMService(), calls


def test_clause_extraction_reads_every_section_and_checks_quotes(service) -> None:  # noqa: ANN001
    llm, calls = service
    result = llm.extract_clauses(CONTRACT)
    coverage = result["data"]["coverage"]
    assert coverage["characters_read"] == coverage["characters"] == len(CONTRACT)
    assert len(calls) == coverage["sections"] + 1  # every section, plus one classification call

    clauses = {c["type"]: c for c in result["data"]["clauses"]}
    assert clauses["Governing Law"]["verification"] == "exact"
    assert clauses["Anti-Assignment"]["verification"] == "not_found"  # the invented quote is caught
    assert result["data"]["parties"] == ["Acme Corp", "Beta LLC"]


def test_duplicate_findings_from_overlapping_sections_are_merged(service) -> None:  # noqa: ANN001
    llm, _ = service
    clauses = llm.extract_clauses(CONTRACT)["data"]["clauses"]
    invented = [c for c in clauses if c["type"] == "Anti-Assignment"]
    assert len(invented) == 1


def test_risk_score_uses_the_most_concerning_section(monkeypatch: pytest.MonkeyPatch) -> None:
    replies = iter([
        {"risk_score": 20, "risks": []},
        {"risk_score": 75, "risks": [{"title": "Assignment", "severity": "high",
                                      "description": "Consent needed",
                                      "quote": "Neither party may assign this Agreement without the prior written consent"}]},
    ])
    monkeypatch.setattr(LLMService, "_execute_completion", lambda self, messages, **kw: json.dumps(next(replies)))
    monkeypatch.setattr(module.settings, "LLM_SECTION_CHARS", len(CONTRACT) // 2 + 400)
    result = LLMService().analyze_risks(CONTRACT)
    assert result["risk_score"] == 75 and result["risk_level"] == "High"
    assert result["risks"][0]["verification"] == "exact"
    assert result["risks"][0]["severity"] == "High"


def test_comparison_lists_only_real_changes() -> None:
    old = "The rent is $2,000 per month. The Tenant may keep one pet. Notice must be given in writing."
    new = "The rent is $2,500 per month. Notice must be given in writing. The Tenant may sublet with consent."
    changes = LLMService.diff_documents(old, new)
    assert changes["modified"] == [{"old": "The rent is $2,000 per month.", "new": "The rent is $2,500 per month."}]
    assert changes["removed"] == [{"old": "The Tenant may keep one pet.", "new": ""}]
    assert changes["added"] == [{"old": "", "new": "The Tenant may sublet with consent."}]


def test_identical_documents_need_no_ai_call(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("the AI should not be called")
    monkeypatch.setattr(LLMService, "_execute_completion", fail)
    result = LLMService().compare_documents("Same text here.", "Same text here.")
    assert result["added"] == result["removed"] == result["modified"] == []
