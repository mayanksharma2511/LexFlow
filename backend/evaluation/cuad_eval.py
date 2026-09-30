"""Evaluate LexFlow's clause extraction against lawyer labels from CUAD.

CUAD (the Contract Understanding Atticus Dataset, CC BY 4.0) contains commercial contracts in
which lawyers marked the passages belonging to 41 clause categories. LexFlow looks for 14 of
them. This script compares two ways of giving a contract to the same model with the same prompt:

- "start_and_end": the first and last 3,500 characters only, as earlier versions of LexFlow did;
- "whole": every section of the contract, as LexFlow does now.

A clause counts as found when LexFlow reports that clause type with a quote that is in the
document and overlaps a passage the lawyers labelled with that type (by at least half of the
shorter of the two).

Commands (run from the backend folder):

    python -m evaluation.cuad_eval visibility      # no API calls
    python -m evaluation.cuad_eval run --contracts 40
    python -m evaluation.cuad_eval report

`run` can be stopped and restarted at any time: every model reply is saved in
evaluation/results/responses.jsonl and reused. When the API's daily limit is reached it stops,
and running it again the next day continues where it left off. The contracts are processed in
a fixed random order, so the contracts finished so far are always a random sample.
"""

import argparse
import bisect
import hashlib
import io
import json
import random
import sys
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import (
    LLMConnectionError,
    LLMQuotaExceededError,
    LLMRateLimitError,
    LLMServiceError,
)
from app.services.ai.grounding import normalize_with_offsets, verify_quote
from app.services.ai.llm_service import CHARS_PER_TOKEN, LLMService, split_into_sections
from app.services.ai.prompts import CLAUSE_EXTRACTION_PROMPT, CLAUSE_TYPES

HERE = Path(__file__).resolve().parent
DATA_FILE = HERE / "data" / "test.json"
RESULTS = HERE / "results"
CACHE_FILE = RESULTS / "responses.jsonl"
CUAD_URL = "https://github.com/TheAtticusProject/cuad/raw/main/data.zip"

SEED = 2027
MAX_CONTRACT_CHARS = 100_000  # longer contracts are left out to fit the free API tier
OLD_WINDOW_CHARS = 7000       # earlier versions sent the first and last 3,500 characters
OLD_TRUNCATION_MARKER = "\n\n[... OCR TEXT TRUNCATED FOR TOKEN LIMITS ...]\n\n"
MIN_OVERLAP = 0.5
MODES = ("start_and_end", "whole")
BOOTSTRAP_SAMPLES = 2000


class StopRun(Exception):
    """The run cannot continue now (daily limit, repeated rate limits, connection problems)."""


# ----- Data -----

def download_cuad() -> None:
    """Download CUAD's test split (102 contracts) into evaluation/data/."""
    if DATA_FILE.exists():
        return
    print(f"Downloading CUAD from {CUAD_URL} ...")
    try:
        with urllib.request.urlopen(CUAD_URL, timeout=120) as response:  # noqa: S310 (fixed https URL)
            archive = zipfile.ZipFile(io.BytesIO(response.read()))
    except OSError as exc:
        sys.exit(
            f"Could not download CUAD ({exc}). Download it with:\n"
            f"  curl -L -o /tmp/cuad.zip {CUAD_URL} && unzip -o -j /tmp/cuad.zip test.json -d {DATA_FILE.parent}"
        )
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_bytes(archive.read("test.json"))


def load_contracts() -> list[dict]:
    """Each contract: title, text, and the lawyer-labelled spans for LexFlow's clause types."""
    download_cuad()
    contracts = []
    for entry in json.loads(DATA_FILE.read_text())["data"]:
        paragraph = entry["paragraphs"][0]
        gold: dict[str, list[tuple[int, int]]] = {}
        for qa in paragraph["qas"]:
            clause_type = qa["id"].split("__")[-1]
            if clause_type in CLAUSE_TYPES and qa["answers"]:
                spans = {(a["answer_start"], a["answer_start"] + len(a["text"])) for a in qa["answers"]}
                gold[clause_type] = sorted(spans)
        contracts.append({"title": entry["title"], "text": paragraph["context"], "gold": gold})
    return contracts


def sample_order(contracts: list[dict]) -> list[dict]:
    """Contracts up to MAX_CONTRACT_CHARS long, in a fixed random order."""
    eligible = sorted((c for c in contracts if len(c["text"]) <= MAX_CONTRACT_CHARS), key=lambda c: c["title"])
    random.Random(SEED).shuffle(eligible)
    return eligible


def model_inputs(text: str, mode: str) -> list[str]:
    if mode == "start_and_end":
        if len(text) <= OLD_WINDOW_CHARS:
            return [text]
        half = OLD_WINDOW_CHARS // 2
        return [text[:half] + OLD_TRUNCATION_MARKER + text[-half:]]
    return [section for _, section in split_into_sections(text)]


def old_window_spans(text: str) -> list[tuple[int, int]]:
    if len(text) <= OLD_WINDOW_CHARS:
        return [(0, len(text))]
    half = OLD_WINDOW_CHARS // 2
    return [(0, half), (len(text) - half, len(text))]


# ----- Model replies (cached) -----

def _key(model_input: str) -> str:
    raw = "\x00".join([settings.LLM_MODEL, CLAUSE_EXTRACTION_PROMPT, model_input])
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def load_cache() -> dict[str, dict]:
    cache: dict[str, dict] = {}
    if CACHE_FILE.exists():
        for line in CACHE_FILE.read_text().splitlines():
            if line.strip():
                record = json.loads(line)
                cache[record["key"]] = record
    return cache


def _ask_model(llm: LLMService, model_input: str) -> dict:
    try:
        content = llm._execute_completion(
            [{"role": "system", "content": CLAUSE_EXTRACTION_PROMPT}, {"role": "user", "content": model_input}],
            json_mode=True,
        )
        return {"content": content, "error": None}
    except LLMQuotaExceededError as exc:
        raise StopRun("The API's daily limit has been reached. Run the same command again tomorrow.") from exc
    except (LLMRateLimitError, LLMConnectionError) as exc:
        raise StopRun(f"{exc} Run the same command again in a few minutes.") from exc
    except LLMServiceError as exc:
        # The model's reply was rejected as invalid JSON: a genuine failure, recorded as such.
        if "json" in str(exc).lower():
            return {"content": None, "error": str(exc)[:300]}
        raise StopRun(str(exc)) from exc


def parse_reply(record: dict) -> list[dict] | None:
    """The clauses in a cached reply, or None if the reply could not be read."""
    try:
        parsed = json.loads(record.get("content") or "")
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return [
        {"type": c["type"], "quote": str(c.get("quote") or "")}
        for c in parsed.get("clauses") or []
        if isinstance(c, dict) and c.get("type") in CLAUSE_TYPES
    ]


def run(n_contracts: int) -> None:
    if not settings.GROQ_API_KEY:
        sys.exit("Set GROQ_API_KEY in backend/.env first.")
    contracts = sample_order(load_contracts())[:n_contracts]
    cache = load_cache()
    todo = [(c, m, x) for c in contracts for m in MODES for x in model_inputs(c["text"], m) if _key(x) not in cache]
    tokens = sum(len(x) / CHARS_PER_TOKEN + (len(CLAUSE_EXTRACTION_PROMPT) / CHARS_PER_TOKEN) + 1000 for _, _, x in todo)
    print(f"Model: {settings.LLM_MODEL}. {len(contracts)} contracts; {len(todo)} model calls left "
          f"(roughly {tokens / 1000:.0f}k tokens).")

    llm = LLMService()
    RESULTS.mkdir(parents=True, exist_ok=True)
    done_calls = 0
    try:
        for index, contract in enumerate(contracts, start=1):
            for mode in MODES:
                inputs = model_inputs(contract["text"], mode)
                for section, model_input in enumerate(inputs, start=1):
                    key = _key(model_input)
                    if key in cache:
                        continue
                    record = {"key": key, "contract": contract["title"], "mode": mode, "section": section,
                              "model": settings.LLM_MODEL, **_ask_model(llm, model_input)}
                    with CACHE_FILE.open("a") as f:
                        f.write(json.dumps(record) + "\n")
                    cache[key] = record
                    done_calls += 1
            print(f"[{index}/{len(contracts)}] {contract['title'][:70]}")
    except StopRun as stop:
        print(f"\nStopped after {done_calls} new call(s): {stop}")
        return
    print("\nAll contracts done. Now run: python -m evaluation.cuad_eval report")


# ----- Scoring -----

def _overlaps(a: tuple[int, int], b: tuple[int, int]) -> bool:
    overlap = min(a[1], b[1]) - max(a[0], b[0])
    shorter = min(a[1] - a[0], b[1] - b[0])
    return shorter > 0 and overlap >= MIN_OVERLAP * shorter


def _to_normalized(offsets: list[int], span: tuple[int, int]) -> tuple[int, int]:
    return bisect.bisect_left(offsets, span[0]), bisect.bisect_left(offsets, span[1])


def score_contract(contract: dict, predictions: list[dict]) -> dict:
    """Per clause type: predictions, correct predictions, quotes not found, and whether the
    lawyer-labelled clause was found."""
    text = contract["text"]
    doc, offsets = normalize_with_offsets(text)
    gold = {t: [_to_normalized(offsets, s) for s in spans] for t, spans in contract["gold"].items()}
    result = {t: {"predicted": 0, "correct": 0, "not_found": 0, "labelled": t in gold,
                  "found": False, "spans": len(gold.get(t, [])), "spans_found": 0} for t in CLAUSE_TYPES}
    found_spans: dict[str, set[int]] = {t: set() for t in CLAUSE_TYPES}
    seen: set[tuple[str, int, int]] = set()
    for p in predictions:
        check = verify_quote(p["quote"], text, doc)
        r = result[p["type"]]
        if check["start"] is None:
            r["predicted"] += 1
            r["not_found"] += 1
            continue
        span = (check["start"], check["end"])
        if (p["type"], *span) in seen:  # the same passage reported twice (e.g. in overlapping sections)
            continue
        seen.add((p["type"], *span))
        r["predicted"] += 1
        hits = [i for i, g in enumerate(gold.get(p["type"], [])) if _overlaps(span, g)]
        if hits:
            r["correct"] += 1
            r["found"] = True
            found_spans[p["type"]].update(hits)
    for t in CLAUSE_TYPES:
        result[t]["spans_found"] = len(found_spans[t])
    return result


def visible_to_old_window(contract: dict) -> dict[str, bool]:
    """For each labelled clause type: is any labelled passage (mostly) inside the old window?"""
    windows = old_window_spans(contract["text"])
    visible = {}
    for t, spans in contract["gold"].items():
        visible[t] = any(
            min(s[1], w[1]) - max(s[0], w[0]) >= MIN_OVERLAP * (s[1] - s[0]) for s in spans for w in windows
        )
    return visible


def _totals(scores: list[dict], types: tuple[str, ...] | list[str] = tuple(CLAUSE_TYPES)) -> dict:
    t = {"predicted": 0, "correct": 0, "not_found": 0, "labelled": 0, "found": 0}
    for s in scores:
        for ct in types:
            r = s[ct]
            t["predicted"] += r["predicted"]
            t["correct"] += r["correct"]
            t["not_found"] += r["not_found"]
            t["labelled"] += int(r["labelled"])
            t["found"] += int(r["labelled"] and r["found"])
    return t


def _rate(a: int, b: int) -> float | None:
    return a / b if b else None


def _pct(x: float | None) -> str:
    return "n/a" if x is None else f"{100 * x:.0f}%"


def bootstrap_recall_difference(whole: list[dict], old: list[dict]) -> tuple[float, float]:
    """95% interval for (whole recall - start_and_end recall), resampling contracts."""
    rng = random.Random(SEED)
    n = len(whole)
    diffs = []
    for _ in range(BOOTSTRAP_SAMPLES):
        idx = [rng.randrange(n) for _ in range(n)]
        w = _totals([whole[i] for i in idx])
        o = _totals([old[i] for i in idx])
        if w["labelled"]:
            diffs.append(w["found"] / w["labelled"] - o["found"] / o["labelled"])
    diffs.sort()
    return diffs[int(0.025 * len(diffs))], diffs[int(0.975 * len(diffs)) - 1]


def report() -> None:
    contracts = sample_order(load_contracts())
    cache = load_cache()
    scored: dict[str, list[dict]] = {m: [] for m in MODES}
    used: list[dict] = []
    calls = {m: 0 for m in MODES}
    unreadable = {m: 0 for m in MODES}
    for contract in contracts:
        keys = {m: [_key(x) for x in model_inputs(contract["text"], m)] for m in MODES}
        if not all(k in cache for m in MODES for k in keys[m]):
            continue  # only contracts finished in both modes are compared
        used.append(contract)
        for m in MODES:
            predictions: list[dict] = []
            for k in keys[m]:
                calls[m] += 1
                clauses = parse_reply(cache[k])
                if clauses is None:
                    unreadable[m] += 1
                else:
                    predictions.extend(clauses)
            scored[m].append(score_contract(contract, predictions))
    if not used:
        sys.exit("No finished contracts yet. Run: python -m evaluation.cuad_eval run")

    totals = {m: _totals(scored[m]) for m in MODES}
    low, high = bootstrap_recall_difference(scored["whole"], scored["start_and_end"])
    visible = [visible_to_old_window(c) for c in used]
    labelled_pairs = sum(len(v) for v in visible)
    visible_pairs = sum(sum(v.values()) for v in visible)

    lines = [
        "# LexFlow clause extraction on CUAD",
        "",
        f"Model `{settings.LLM_MODEL}` (Groq), the same prompt in both modes, run {date.today().isoformat()}.",
        f"{len(used)} contracts from CUAD's test split, in a fixed random order (seed {SEED}), "
        f"excluding contracts over {MAX_CONTRACT_CHARS:,} characters.",
        "",
        "A labelled clause counts as found when LexFlow reports that clause type with a quote that is in the",
        "document and overlaps a passage the lawyers labelled with that type.",
        "",
        "| Input given to the model | Labelled clauses found | Findings that match a label | Quotes not in the document | Unreadable replies |",
        "|---|---|---|---|---|",
    ]
    names = {"start_and_end": "First and last 3,500 characters (earlier LexFlow)", "whole": "Whole contract, in sections (LexFlow now)"}
    for m in MODES:
        t = totals[m]
        lines.append(
            f"| {names[m]} | {t['found']} of {t['labelled']} ({_pct(_rate(t['found'], t['labelled']))}) "
            f"| {_pct(_rate(t['correct'], t['predicted']))} of {t['predicted']} "
            f"| {t['not_found']} of {t['predicted']} ({_pct(_rate(t['not_found'], t['predicted']))}) "
            f"| {unreadable[m]} of {calls[m]} |"
        )
    lines += [
        "",
        f"Difference in labelled clauses found (whole minus start and end): "
        f"{100 * (totals['whole']['found'] / totals['whole']['labelled'] - totals['start_and_end']['found'] / totals['start_and_end']['labelled']):+.0f} "
        f"percentage points (95% bootstrap interval over contracts: {100 * low:+.0f} to {100 * high:+.0f}).",
        "",
        f"Only {visible_pairs} of the {labelled_pairs} labelled clauses ({_pct(_rate(visible_pairs, labelled_pairs))}) "
        "lie mostly inside the first and last 3,500 characters, so that is the most the earlier input could find.",
        "",
        "## By clause type",
        "",
        "| Clause type | Contracts with a label | Found (whole) | Found (start and end) | Visible in start and end |",
        "|---|---|---|---|---|",
    ]
    for ct in CLAUSE_TYPES:
        w, o = _totals(scored["whole"], [ct]), _totals(scored["start_and_end"], [ct])
        vis = sum(v.get(ct, False) for v in visible)
        if w["labelled"]:
            lines.append(f"| {ct} | {w['labelled']} | {_pct(_rate(w['found'], w['labelled']))} "
                         f"| {_pct(_rate(o['found'], o['labelled']))} | {_pct(_rate(vis, w['labelled']))} |")
    lines += [
        "",
        "Notes: \"Findings that match a label\" is a lower bound on precision, because CUAD's lawyers did not",
        "label every passage that could fit a category. Risk scores are not evaluated here: there are no expert",
        "labels for them.",
        "",
    ]
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "cuad_results.md").write_text("\n".join(lines))
    summary = {
        "model": settings.LLM_MODEL, "contracts": len(used), "seed": SEED,
        "totals": totals, "unreadable_replies": unreadable, "calls": calls,
        "recall_difference_ci95": [low, high],
        "labelled_clauses": labelled_pairs, "visible_to_start_and_end": visible_pairs,
        "contract_titles": [c["title"] for c in used],
    }
    (RESULTS / "cuad_results.json").write_text(json.dumps(summary, indent=2))
    print("\n".join(lines))
    print(f"Saved to {RESULTS / 'cuad_results.md'}")


def visibility() -> None:
    """How many labelled clauses the earlier input (first and last 3,500 characters) could see,
    over all 102 test contracts. Needs no API calls."""
    contracts = load_contracts()
    per_type: dict[str, list[int]] = {t: [0, 0] for t in CLAUSE_TYPES}
    for c in contracts:
        for t, is_visible in visible_to_old_window(c).items():
            per_type[t][0] += int(is_visible)
            per_type[t][1] += 1
    labelled = sum(v[1] for v in per_type.values())
    seen = sum(v[0] for v in per_type.values())
    lengths = sorted(len(c["text"]) for c in contracts)
    print(f"{len(contracts)} CUAD test contracts; median length {lengths[len(lengths) // 2]:,} characters.")
    print(f"Labelled clauses mostly inside the first and last 3,500 characters: {seen} of {labelled} ({_pct(seen / labelled)}).\n")
    for t, (v, n) in per_type.items():
        if n:
            print(f"  {t:<28} {v:>3} of {n:>3} ({_pct(v / n)})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run", help="call the model (resumable)")
    run_parser.add_argument("--contracts", type=int, default=40)
    sub.add_parser("report", help="score the saved replies")
    sub.add_parser("visibility", help="what the earlier input could see (no API calls)")
    args = parser.parse_args()
    if args.command == "run":
        run(args.contracts)
    elif args.command == "report":
        report()
    else:
        visibility()


if __name__ == "__main__":
    main()
