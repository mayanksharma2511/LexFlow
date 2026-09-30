"""Quotes from the AI are checked against the document before they are shown."""

from app.services.ai.grounding import verify_quote

DOCUMENT = (
    "This Agreement shall be governed by and construed in accordance with the laws of the "
    "State of Delaware. Either party may terminate this Agreement for convenience upon ninety "
    "(90) days’ prior written notice to the other party."
)


def test_exact_quote_is_verified_despite_case_spacing_and_curly_quotes() -> None:
    quote = "either party may terminate   this agreement for convenience upon ninety (90) days' prior written notice"
    assert verify_quote(quote, DOCUMENT)["status"] == "exact"


def test_small_differences_are_a_close_match() -> None:
    quote = "Either party may terminate this Agreement for convenience upon ninety (90) days prior notice to the other party"
    assert verify_quote(quote, DOCUMENT)["status"] == "close"


def test_invented_text_is_not_found() -> None:
    quote = "The Supplier shall indemnify the Buyer for all losses caused by late delivery."
    assert verify_quote(quote, DOCUMENT)["status"] == "not_found"


def test_very_short_quotes_do_not_count() -> None:
    assert verify_quote("Delaware", DOCUMENT)["status"] == "not_found"
