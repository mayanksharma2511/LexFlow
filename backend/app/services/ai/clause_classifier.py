"""A clause classifier trained on lawyer-labelled contracts (CUAD), used when the AI is unavailable.

The model is trained by `python -m evaluation.clause_classifier`, which also measures it on CUAD's
test contracts, and saved to backend/ml/clause_classifier.joblib. If that file is missing, LexFlow
falls back to simple text patterns instead.
"""

import logging
import re
from functools import lru_cache
from pathlib import Path

import numpy as np

from app.services.ai.prompts import CLAUSE_TYPES

logger = logging.getLogger(__name__)

MODEL_FILE = Path(__file__).resolve().parents[3] / "ml" / "clause_classifier.joblib"
MIN_PASSAGE_CHARS = 40
_BREAK = re.compile(r"\n\s*\n|(?<=[.;:])\s+(?=[A-Z0-9(\"'])")


def passages(text: str) -> list[tuple[int, int]]:
    """Split a document into passages (start, end), roughly sentences, merging very short
    pieces such as headings into the passage that follows them."""
    pieces: list[tuple[int, int]] = []
    start = 0
    for match in _BREAK.finditer(text):
        pieces.append((start, match.start()))
        start = match.end()
    pieces.append((start, len(text)))

    merged: list[tuple[int, int]] = []
    pending: int | None = None
    for s, e in pieces:
        if not text[s:e].strip():
            continue
        s = pending if pending is not None else s
        if len(text[s:e].strip()) < MIN_PASSAGE_CHARS:
            pending = s
            continue
        merged.append((s, e))
        pending = None
    if pending is not None:
        merged.append((pending, len(text)))
    return merged


def probabilities(bundle: dict, texts: list[str]) -> np.ndarray:
    """Passages x clause types: the model's probability that a passage is that clause."""
    out = np.zeros((len(texts), len(bundle["types"])))
    if not texts:
        return out
    X = bundle["vectorizer"].transform(texts)
    for j, model in enumerate(bundle["models"]):
        if model is not None:
            out[:, j] = model.predict_proba(X)[:, 1]
    return out


def select(text: str, spans: list[tuple[int, int]], probs: np.ndarray, bundle: dict) -> list[dict]:
    """For each clause type, the most likely passages above that type's tuned threshold."""
    found = []
    for j, clause_type in enumerate(bundle["types"]):
        threshold, top_k = bundle["settings"][clause_type]
        for i in np.argsort(-probs[:, j])[:top_k]:
            if probs[i, j] >= threshold:
                found.append({
                    "type": clause_type,
                    "quote": text[spans[i][0]:spans[i][1]].strip(),
                    "probability": round(float(probs[i, j]), 2),
                })
    return found


@lru_cache(maxsize=1)
def load_model() -> dict | None:
    if not MODEL_FILE.exists():
        return None
    try:
        import joblib

        bundle = joblib.load(MODEL_FILE)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not load the clause classifier: %s", exc)
        return None
    if list(bundle.get("types", [])) != list(CLAUSE_TYPES):
        logger.warning("The saved clause classifier uses different clause types; retrain it.")
        return None
    return bundle


def find_clauses(text: str) -> list[dict] | None:
    """Clauses found by the trained classifier, or None if no trained model is available."""
    bundle = load_model()
    if bundle is None:
        return None
    spans = passages(text or "")
    probs = probabilities(bundle, [text[s:e] for s, e in spans])
    return select(text, spans, probs, bundle)
