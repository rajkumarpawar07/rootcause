"""End-to-end validation of stages 1-3 against expected_cluster labels.

Runs the demo dataset (brief section 9) through extract -> embed -> cluster,
then compares the predicted grouping with the hand-written expected labels:
purity via optimal one-to-one mapping plus adjusted Rand index.

Usage (from backend/):
    python -m pipeline.validate [--min-cluster-size N] [--skip-extract]
"""

import argparse
import hashlib
import json
import sys
import time
import warnings
from collections import Counter, defaultdict
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")

import numpy as np
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score

from .cluster import NOISE_CLUSTER_ID, run_stage3
from .embed import embed_reasoning

# Exit gate is a REGRESSION tripwire, not an absolute quality bar: stage-1
# draw drift and dataset difficulty put measured purity anywhere from
# ~0.47 to 0.80 across documented runs (see README). Default sits below
# every observed good draw so only real regressions fail CI.
DEFAULT_MIN_PURITY = 0.40

DEMO_DATA = Path(__file__).resolve().parents[2] / "demo_data" / "synthetic_responses.json"
STAGE1_CACHE = Path(__file__).resolve().parents[2] / "demo_data" / "stage1_cache.json"


def load_demo_dataset() -> list[dict]:
    with open(DEMO_DATA, encoding="utf-8") as f:
        return json.load(f)


def _cache_key(question: str, response: str) -> str:
    from .extract import summary_word_limit

    limit = summary_word_limit()
    suffix = f"||limit={limit}" if limit > 0 else ""
    return hashlib.sha256(f"{question}||{response}{suffix}".encode("utf-8")).hexdigest()


def extract_cached(question: str, dataset: list[dict], refresh: bool = False) -> list[dict]:
    """Stage 1 with a local summary cache so validation iterations don't
    re-pay LLM latency for identical responses."""
    cache = {} if refresh or not STAGE1_CACHE.exists() else json.loads(
        STAGE1_CACHE.read_text(encoding="utf-8")
    )
    missing = [d for d in dataset if _cache_key(question, d["response"]) not in cache]
    if missing:
        from .extract import extract_batch

        print(f"Stage 1: extracting reasoning ({len(missing)} LLM calls)...")
        t0 = time.time()
        for rec in extract_batch(question, missing):
            cache[_cache_key(question, rec["response_text"])] = rec["reasoning_summary"]
        STAGE1_CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Stage 1 done in {time.time() - t0:.1f}s")
    else:
        print("Stage 1: all summaries served from cache")

    return [
        {
            "student_id": d["student_id"],
            "response_text": d["response"],
            "reasoning_summary": cache[_cache_key(question, d["response"])],
        }
        for d in dataset
    ]


def agreement_report(expected: list[str], predicted: np.ndarray) -> dict:
    n = len(expected)
    true_ids = sorted(set(expected))
    pred_ids = sorted(set(predicted.tolist()))

    # Optimal one-to-one mapping between predicted and expected groups,
    # maximizing matched pairs (Hungarian algorithm). Noise is excluded
    # from the mapping and reported separately.
    matrix = np.zeros((len(pred_ids), len(true_ids)), dtype=int)
    for p_idx, p in enumerate(pred_ids):
        for t_idx, t in enumerate(true_ids):
            matrix[p_idx, t_idx] = sum(
                1 for pe, te in zip(predicted.tolist(), expected) if pe == p and te == t
            )

    row_ind, col_ind = linear_sum_assignment(-matrix)
    mapping = {
        pred_ids[p_idx]: true_ids[t_idx]
        for p_idx, t_idx in zip(row_ind, col_ind)
        if pred_ids[p_idx] != NOISE_CLUSTER_ID
    }

    mapped = [
        mapping.get(p, "noise" if p == NOISE_CLUSTER_ID else f"unmapped_{p}")
        for p in predicted.tolist()
    ]
    purity = sum(1 for m, t in zip(mapped, expected) if m == t) / n
    ari = adjusted_rand_score(expected, predicted.tolist())

    confusion = defaultdict(Counter)
    for p, t in zip(predicted.tolist(), expected):
        confusion[t][mapping.get(p, "noise")] += 1

    return {
        "purity": purity,
        "ari": ari,
        "mapping": mapping,
        "confusion": {t: dict(c) for t, c in sorted(confusion.items())},
        "noise_count": int((predicted == NOISE_CLUSTER_ID).sum()),
    }


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-cluster-size", type=int, default=3)
    parser.add_argument(
        "--skip-extract",
        action="store_true",
        help="embed raw responses directly (skips stage 1 LLM calls)",
    )
    parser.add_argument(
        "--refresh-cache",
        action="store_true",
        help="ignore the stage-1 cache and re-run LLM extraction",
    )
    parser.add_argument(
        "--dataset",
        default=str(DEMO_DATA),
        help="path to a labeled dataset JSON (default: the section-9 seed set)",
    )
    parser.add_argument(
        "--with-labels",
        action="store_true",
        help="also run stage 4 (cluster labeling) and print the cards",
    )
    parser.add_argument(
        "--min-purity",
        type=float,
        default=DEFAULT_MIN_PURITY,
        help=(
            "exit 1 when purity falls below this (regression tripwire; "
            f"default {DEFAULT_MIN_PURITY}). With --with-labels the gate "
            "uses post-audit purity — what actually ships to the dashboard."
        ),
    )
    args = parser.parse_args()

    dataset = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    question = "Why does ice float on water?"
    print(f"Loaded {len(dataset)} responses from {args.dataset}")

    start = time.time()
    if args.skip_extract:
        records = [
            {
                "student_id": d["student_id"],
                "response_text": d["response"],
                "reasoning_summary": "",
            }
            for d in dataset
        ]
        print("SKIP-EXTRACT mode: embedding raw responses only")
    else:
        records = extract_cached(question, dataset, refresh=args.refresh_cache)

    t_embed = time.time()
    print("Stage 2: embedding reasoning summaries...")
    embeddings = embed_reasoning(records, include_response_text=not args.skip_extract)
    print(f"Stage 2 done in {time.time() - t_embed:.1f}s ({embeddings.shape[1]}-d vectors)")

    t_cluster = time.time()
    print(f"Stage 3: HDBSCAN (min_cluster_size={args.min_cluster_size})...")
    result = run_stage3(records, embeddings)
    print(f"Stage 3 done in {time.time() - t_cluster:.1f}s")

    print("\nClusters found:")
    for c in result.clusters:
        tag = "noise/outliers" if c["cluster_id"] == NOISE_CLUSTER_ID else "cluster"
        print(f"  {tag} {c['cluster_id']}: {c['size']} students -> {c['student_ids']}")

    report = agreement_report([d["expected_cluster"] for d in dataset], result.labels)

    print("\n--- Agreement vs expected_cluster ---")
    print(f"Purity (optimal mapping): {report['purity']:.3f}")
    print(f"Adjusted Rand index:      {report['ari']:.3f}")
    print(f"Noise points:             {report['noise_count']}")
    print("Predicted->expected mapping:")
    for pred_id, exp in sorted(report["mapping"].items()):
        print(f"  cluster {pred_id} -> {exp}")
    print("Confusion (expected: {predicted_group: count}):")
    for expected_label, counts in report["confusion"].items():
        print(f"  {expected_label}: {dict(counts)}")

    mismatches: list[tuple[str, str, str]] = []
    mapped_labels = [
        report["mapping"].get(p, "noise") for p in result.labels.tolist()
    ]
    for rec, d, m in zip(records, dataset, mapped_labels):
        if m != d["expected_cluster"]:
            mismatches.append((rec["student_id"], d["expected_cluster"], m))
    if mismatches:
        print(f"\n{len(mismatches)} mismatched students:")
        for sid, expected_label, got in mismatches:
            resp = next(d["response"] for d in dataset if d["student_id"] == sid)
            summary = next(r["reasoning_summary"] for r in records if r["student_id"] == sid)
            print(f"  {sid}: expected={expected_label} got={got}")
            print(f"       response: {resp}")
            print(f"       reasoning: {summary}")
    else:
        print("\nAll students grouped with their expected misconception.")

    if args.with_labels:
        from .label import run_stage4

        correct_concept = "Density determines whether an object floats"
        print("\nStage 4: labeling clusters (live LLM calls)...")
        cards = run_stage4(question, correct_concept, records, result)
        print("\n--- Dashboard cards (stage 4 output) ---")
        for c in cards:
            badge = {
                "misconception": "Misconception",
                "solid_understanding": "Solid understanding",
                "unclear": "Unclear",
            }.get(c.get("category"), c.get("category", "?"))
            print(f"\n  [{badge}] {c['label']}  ({c['size']} · {c['percentage']}%)")
            print(f"    example: \"{c['example_response']}\"")
            if c.get("gap"):
                print(f"    gap: {c['gap']}")
            print(f"    reteach: {c['reteach_suggestion']}")
            member_ids = set(c["student_ids"])
            member_expected = {
                d["expected_cluster"] for d in dataset if d["student_id"] in member_ids
            }
            counts_by_expected = {
                e: sum(1 for d in dataset if d["student_id"] in member_ids and d["expected_cluster"] == e)
                for e in member_expected
            }
            dominant = max(counts_by_expected, key=counts_by_expected.get)
            expected_badge = (
                "solid_understanding" if dominant == "correct" else "misconception"
            )
            marker = (
                "ok"
                if c.get("category") == expected_badge or c.get("category") == "unclear"
                else f"MISMATCH (dominant={dominant})"
            )
            print(f"    composition: {counts_by_expected} -> {marker}")

        # Post-audit agreement: regroup students by final card and re-score.
        sid_to_card = {
            sid: idx for idx, c in enumerate(cards) for sid in c["student_ids"]
        }
        audited_labels = np.array(
            [sid_to_card.get(d["student_id"], NOISE_CLUSTER_ID) for d in dataset]
        )
        post = agreement_report([d["expected_cluster"] for d in dataset], audited_labels)
        print("\n--- Agreement AFTER stage-4 audit ---")
        print(f"Purity: {post['purity']:.3f}  ARI: {post['ari']:.3f}  (pre-audit purity {report['purity']:.3f})")

    total_time = time.time() - start
    print(f"\nTotal pipeline time: {total_time:.1f}s")

    gate_value = post["purity"] if args.with_labels else report["purity"]
    gate_name = "post-audit" if args.with_labels else "stage-3"
    passed = gate_value >= args.min_purity
    print(
        f"\nExit gate ({gate_name} purity {gate_value:.3f} "
        f"vs min {args.min_purity:.2f}): {'PASS' if passed else 'FAIL'}"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
