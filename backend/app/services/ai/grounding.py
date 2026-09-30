"""Check that text the AI quotes really appears in the document.

The AI is asked to support every clause and risk with a word-for-word quote. A quote is
checked against the document after normalising things that do not change meaning
(letter case, whitespace, curly quotes and dashes):

- "exact": the quote appears in the document as written;
- "close": a passage of the document matches the quote at least CLOSE_MATCH_THRESHOLD
  out of 100 (small differences such as a dropped word or an OCR error);
- "not_found": nothing in the document matches closely enough. The AI may have
  paraphrased or invented the text, so it should not be trusted without checking.
"""

import re

from rapidfuzz import fuzz

CLOSE_MATCH_THRESHOLD = 90
MIN_QUOTE_CHARS = 12  # shorter quotes match too easily to mean anything

_REPLACEMENTS = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", " ": " ",
}


def normalize(text: str) -> str:
    """Lower-case, unify quotes and dashes, and collapse whitespace."""
    for old, new in _REPLACEMENTS.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text).strip().lower()


def verify_quote(quote: str, document: str, normalized_document: str | None = None) -> dict:
    """Return {"status": "exact" | "close" | "not_found", "score": 0-100, "start": int | None}.

    `start` is the position of the match in the normalised document, when there is one.
    Pass `normalized_document` when checking many quotes against the same document.
    """
    q = normalize(quote or "").strip(" .,;:\"'")
    doc = normalized_document if normalized_document is not None else normalize(document)
    if len(q) < MIN_QUOTE_CHARS or not doc:
        return {"status": "not_found", "score": 0.0, "start": None}

    position = doc.find(q)
    if position >= 0:
        return {"status": "exact", "score": 100.0, "start": position}

    alignment = fuzz.partial_ratio_alignment(q, doc, score_cutoff=CLOSE_MATCH_THRESHOLD)
    if alignment is not None:
        return {"status": "close", "score": round(alignment.score, 1), "start": alignment.dest_start}
    return {"status": "not_found", "score": 0.0, "start": None}
