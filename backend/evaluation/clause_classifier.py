"""A clause classifier trained on CUAD's 408 training contracts, as a baseline for the LLM.

Each contract is split into passages (roughly sentences). A passage is labelled with a clause
type when it overlaps a passage the lawyers labelled with that type. A TF-IDF representation and
one logistic regression per clause type are trained on the training contracts only; the 102 test
contracts used to evaluate the LLM are never seen during training or tuning.

For each clause type, the decision threshold and the number of passages reported per contract are
chosen on a validation split of the training contracts. The test contracts are then scored with
exactly the same rule as the LLM (see cuad_eval.score_contract).

    python -m evaluation.clause_classifier                # trains (a few minutes) and reports
    python -m evaluation.clause_classifier --report-only  # reports with the saved model

No API calls are made.
"""

import argparse
import random
import time

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity

from app.services.ai.clause_classifier import MODEL_FILE, passages, probabilities, select
from app.services.ai.prompts import CLAUSE_TYPES
from evaluation.cuad_eval import (
    MODES,
    RESULTS,
    SEED,
    _key,
    _overlaps,
    _pct,
    _rate,
    _totals,
    bootstrap_recall_difference,
    load_cache,
    load_contracts,
    model_inputs,
    parse_reply,
    sample_order,
    score_contract,
)

TYPES = list(CLAUSE_TYPES)
VALIDATION_SHARE = 0.2
THRESHOLDS = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
TOP_K = [1, 2, 3]
NEAR_DUPLICATE = 0.9  # cosine similarity between whole contracts


def passage_labels(contract: dict, spans: list[tuple[int, int]]) -> np.ndarray:
    """A passages x types 0/1 matrix: does the passage overlap a labelled passage of that type?"""
    y = np.zeros((len(spans), len(TYPES)), dtype=np.int8)
    for j, t in enumerate(TYPES):
        for g in contract["gold"].get(t, []):
            for i, p in enumerate(spans):
                if _overlaps(p, g):
                    y[i, j] = 1
    return y


def build(contracts: list[dict]) -> tuple[list[str], np.ndarray, list[tuple[int, list[tuple[int, int]]]]]:
    texts: list[str] = []
    labels = []
    index = []
    for c in contracts:
        spans = passages(c["text"])
        index.append((len(texts), spans))
        texts.extend(c["text"][s:e] for s, e in spans)
        labels.append(passage_labels(c, spans))
    return texts, np.vstack(labels), index


def fit(texts: list[str], y: np.ndarray) -> tuple[TfidfVectorizer, list[LogisticRegression | None]]:
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.5, sublinear_tf=True, max_features=200_000)
    X = vectorizer.fit_transform(texts)
    models: list[LogisticRegression | None] = []
    for j in range(len(TYPES)):
        if y[:, j].sum() == 0:
            models.append(None)
            continue
        model = LogisticRegression(C=4.0, class_weight="balanced", max_iter=2000)
        model.fit(X, y[:, j])
        models.append(model)
    return vectorizer, models


def predict(contract_text: str, spans: list[tuple[int, int]], probs: np.ndarray, settings: dict) -> list[dict]:
    """The passages reported for one contract, as {"type", "quote"} like the LLM's findings."""
    return select(contract_text, spans, probs, {"types": TYPES, "settings": settings})


def tune(contracts: list[dict], probs: np.ndarray, index: list) -> dict[str, tuple[float, int]]:
    """Per clause type, the threshold and passages-per-contract that give the best F1 on the
    validation contracts, using the same scoring rule as the test."""
    settings = {}
    for j, t in enumerate(TYPES):
        best = (-1.0, 0.5, 1)
        for threshold in THRESHOLDS:
            for top_k in TOP_K:
                trial = {tt: (1.1, 1) for tt in TYPES}
                trial[t] = (threshold, top_k)
                totals = {"predicted": 0, "correct": 0, "labelled": 0, "found": 0}
                for c, (offset, spans) in zip(contracts, index):
                    p = probs[offset:offset + len(spans)]
                    r = score_contract(c, predict(c["text"], spans, p, trial))[t]
                    totals["predicted"] += r["predicted"]
                    totals["correct"] += r["correct"]
                    totals["labelled"] += int(r["labelled"])
                    totals["found"] += int(r["labelled"] and r["found"])
                precision = _rate(totals["correct"], totals["predicted"]) or 0.0
                recall = _rate(totals["found"], totals["labelled"]) or 0.0
                f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
                if f1 > best[0]:
                    best = (f1, threshold, top_k)
        settings[t] = (best[1], best[2])
    return settings


def train() -> dict:
    train_contracts = load_contracts("train_separate_questions.json")
    rng = random.Random(SEED)
    shuffled = sorted(train_contracts, key=lambda c: c["title"])
    rng.shuffle(shuffled)
    n_val = int(len(shuffled) * VALIDATION_SHARE)
    validation, fitting = shuffled[:n_val], shuffled[n_val:]

    print(f"Tuning on {len(fitting)} training contracts, validating on {len(validation)} ...")
    texts, y, _ = build(fitting)
    vectorizer, models = fit(texts, y)
    val_texts, _, val_index = build(validation)
    settings = tune(validation, probabilities({"vectorizer": vectorizer, "models": models, "types": TYPES}, val_texts), val_index)

    print(f"Refitting on all {len(train_contracts)} training contracts ...")
    texts, y, _ = build(train_contracts)
    vectorizer, models = fit(texts, y)
    bundle = {"vectorizer": vectorizer, "models": models, "settings": settings, "types": TYPES,
              "training_contracts": len(train_contracts), "training_passages": len(texts)}
    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, MODEL_FILE, compress=3)
    return bundle


def score_classifier(bundle: dict, contracts: list[dict], strict: bool = False) -> tuple[list[dict], float]:
    scores = []
    start = time.perf_counter()
    for c in contracts:
        spans = passages(c["text"])
        probs = probabilities(bundle, [c["text"][s:e] for s, e in spans])
        scores.append(score_contract(c, select(c["text"], spans, probs, bundle), strict))
    seconds = (time.perf_counter() - start) / max(len(contracts), 1)
    return scores, seconds


def _row(name: str, scores: list[dict]) -> str:
    t = _totals(scores)
    return (f"| {name} | {t['found']} of {t['labelled']} ({_pct(_rate(t['found'], t['labelled']))}) "
            f"| {_pct(_rate(t['correct'], t['predicted']))} of {t['predicted']} |")


def llm_scores(
    contracts: list[dict], strict: bool = False, bundle: dict | None = None
) -> tuple[list[dict], dict[str, list[dict]]]:
    """The contracts the LLM has finished in both modes, and its scores on them. With a classifier
    bundle, also scores the LLM's whole-contract findings and the classifier's findings together
    ("both")."""
    cache = load_cache()
    finished: list[dict] = []
    scores: dict[str, list[dict]] = {m: [] for m in (*MODES, "both")}
    for c in sample_order(contracts):
        keys = {m: [_key(x) for x in model_inputs(c["text"], m)] for m in MODES}
        if all(k in cache for m in MODES for k in keys[m]):
            finished.append(c)
            for m in MODES:
                predictions: list[dict] = []
                for k in keys[m]:
                    predictions.extend(parse_reply(cache[k]) or [])
                scores[m].append(score_contract(c, predictions, strict))
                if m == "whole" and bundle is not None:
                    scores["both"].append(score_contract(c, predictions + find_in(bundle, c["text"]), strict))
    return finished, scores


def near_duplicates(test: list[dict], train_contracts: list[dict]) -> list[bool]:
    """For each test contract: is a training contract almost the same document?"""
    vectorizer = TfidfVectorizer(sublinear_tf=True, min_df=2).fit([c["text"] for c in train_contracts + test])
    similarity = cosine_similarity(
        vectorizer.transform([c["text"] for c in test]), vectorizer.transform([c["text"] for c in train_contracts])
    )
    return list(similarity.max(axis=1) >= NEAR_DUPLICATE)


def report(bundle: dict) -> None:
    test = load_contracts()
    all_scores, seconds = score_classifier(bundle, test)
    finished, llm = llm_scores(test, bundle=bundle)
    clf_scores, _ = score_classifier(bundle, finished)

    lines = [
        "# Trained clause classifier on CUAD",
        "",
        f"TF-IDF and logistic regression, trained on CUAD's {bundle['training_contracts']} training contracts "
        f"({bundle['training_passages']:,} passages). Thresholds were tuned on a validation split of the training "
        "contracts; the test contracts were not used for training or tuning. Findings are scored with the same rule as "
        f"the LLM (evaluation/cuad_eval.py). No API calls; about {seconds:.2f} seconds per contract.",
        "",
        f"## All {len(test)} test contracts",
        "",
        "| Method | Labelled clauses found | Findings that match a label |",
        "|---|---|---|",
        _row("Trained classifier", all_scores),
        "",
    ]
    if finished:
        low, high = bootstrap_recall_difference(clf_scores, llm["whole"])
        lines += [
            f"## Compared with the LLM on the {len(finished)} contracts it has finished",
            "",
            "| Method | Labelled clauses found | Findings that match a label |",
            "|---|---|---|",
            _row("Trained classifier (no API calls)", clf_scores),
            _row("LLM, first and last 3,500 characters", llm["start_and_end"]),
            _row("LLM, whole contract in sections", llm["whole"]),
            _row("LLM (whole contract) and classifier together", llm["both"]),
            "",
            f"Classifier minus LLM (whole contract), labelled clauses found: 95% bootstrap interval over contracts "
            f"{100 * low:+.0f} to {100 * high:+.0f} percentage points.",
            "",
        ]

    duplicate = near_duplicates(test, load_contracts("train_separate_questions.json"))
    kept = [s for s, d in zip(all_scores, duplicate) if not d]
    lines += [
        "## Checks",
        "",
        f"- **Near-duplicate contracts.** {sum(duplicate)} test contract(s) closely match a training contract "
        f"(cosine similarity of at least {NEAR_DUPLICATE}). Without them the classifier finds "
        f"{_pct(_rate(_totals(kept)['found'], _totals(kept)['labelled']))} of labelled clauses.",
    ]
    strict_all, _ = score_classifier(bundle, test, strict=True)
    t = _totals(strict_all)
    lines.append(
        f"- **Stricter matching** (at least half of each finding must lie inside the labelled passage): the classifier "
        f"finds {_pct(_rate(t['found'], t['labelled']))} of labelled clauses on all test contracts."
    )
    if finished:
        strict_clf, _ = score_classifier(bundle, finished, strict=True)
        _, strict_llm = llm_scores(test, strict=True, bundle=bundle)
        c, w, b = _totals(strict_clf), _totals(strict_llm["whole"]), _totals(strict_llm["both"])
        lines.append(
            f"  On the {len(finished)} finished contracts: classifier {_pct(_rate(c['found'], c['labelled']))}, "
            f"LLM (whole contract) {_pct(_rate(w['found'], w['labelled']))}, "
            f"both together {_pct(_rate(b['found'], b['labelled']))}."
        )
    lengths = [len(f["quote"]) for c in test for f in find_in(bundle, c["text"])]
    lines += [
        f"- **Finding length.** Median {int(np.median(lengths))} characters per classifier finding, so it is not "
        "matching labels by returning long stretches of text.",
        "",
        "## By clause type (all test contracts)",
        "",
        "| Clause type | Contracts with a label | Found | Threshold | Passages per contract |",
        "|---|---|---|---|---|",
    ]
    for ct in TYPES:
        s = _totals(all_scores, [ct])
        threshold, top_k = bundle["settings"][ct]
        if s["labelled"]:
            lines.append(f"| {ct} | {s['labelled']} | {_pct(_rate(s['found'], s['labelled']))} | {threshold} | {top_k} |")
    lines.append("")
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "classifier_results.md").write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"Saved to {RESULTS / 'classifier_results.md'}")


def find_in(bundle: dict, text: str) -> list[dict]:
    spans = passages(text)
    return select(text, spans, probabilities(bundle, [text[s:e] for s, e in spans]), bundle)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the clause classifier on CUAD and report its results.")
    parser.add_argument("--report-only", action="store_true", help="use the saved model instead of retraining")
    args = parser.parse_args()
    if args.report_only and MODEL_FILE.exists():
        report(joblib.load(MODEL_FILE))
    else:
        report(train())


if __name__ == "__main__":
    main()
