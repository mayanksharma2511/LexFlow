"""Scoring used by the CUAD evaluation (evaluation/cuad_eval.py). No data download or API calls."""

from evaluation.cuad_eval import model_inputs, score_contract, visible_to_old_window

GOVERNING = "This Agreement shall be governed by the laws of the State of Delaware."
ASSIGNMENT = "Neither party may assign this Agreement without the prior written consent of the other party."
TEXT = "SUPPLY AGREEMENT.  " + "Deliveries are made weekly. " * 400 + GOVERNING + " " + "Invoices are paid monthly. " * 400 + ASSIGNMENT


def _contract() -> dict:
    g = TEXT.index(GOVERNING)
    a = TEXT.index(ASSIGNMENT)
    return {
        "title": "test",
        "text": TEXT,
        "gold": {"Governing Law": [(g, g + len(GOVERNING))], "Anti-Assignment": [(a, a + len(ASSIGNMENT))]},
    }


def test_a_matching_quote_finds_the_labelled_clause() -> None:
    result = score_contract(_contract(), [{"type": "Governing Law", "quote": "governed by the laws of the State of Delaware"}])
    assert result["Governing Law"] == {**result["Governing Law"], "predicted": 1, "correct": 1, "found": True}
    assert result["Anti-Assignment"]["labelled"] and not result["Anti-Assignment"]["found"]


def test_wrong_type_invented_quote_and_duplicates_are_not_credited() -> None:
    predictions = [
        {"type": "Anti-Assignment", "quote": GOVERNING},                                  # wrong type
        {"type": "Governing Law", "quote": "This contract is governed by French law."},   # not in document
        {"type": "Governing Law", "quote": GOVERNING},
        {"type": "Governing Law", "quote": GOVERNING},                                    # duplicate
    ]
    result = score_contract(_contract(), predictions)
    assert result["Anti-Assignment"]["correct"] == 0 and result["Anti-Assignment"]["predicted"] == 1
    assert result["Governing Law"]["predicted"] == 2          # duplicate ignored
    assert result["Governing Law"]["not_found"] == 1
    assert result["Governing Law"]["correct"] == 1


def test_old_input_sees_only_the_start_and_end() -> None:
    contract = _contract()
    visible = visible_to_old_window(contract)
    assert visible == {"Governing Law": False, "Anti-Assignment": True}
    (old_input,) = model_inputs(TEXT, "start_and_end")
    assert GOVERNING not in old_input and ASSIGNMENT in old_input
    assert any(GOVERNING in section for section in model_inputs(TEXT, "whole"))
