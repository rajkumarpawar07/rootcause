"""Grow the §9 seed dataset to a full class (~30 responses).

Generates new variations per misconception category with stealth/ox-alpha
via OpenRouter, then merges them with the original seed into an expanded
labeled dataset for pipeline validation at demo scale.

Usage (from backend/):
    python -m pipeline.generate_data            # writes demo_data/synthetic_responses_30.json
    python -m pipeline.generate_data --refresh  # regenerate even if output exists
"""

import argparse
import json
import os
import sys
from pathlib import Path

import httpx

from .extract import chat_completion, parse_json_response

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
SEED_FILE = ROOT / "demo_data" / "synthetic_responses.json"
OUT_FILE = ROOT / "demo_data" / "synthetic_responses_30.json"

# Target distribution matches the brief's walkthrough (section 2):
# half the class holds the majority misconception, only three reason correctly.
CATEGORY_TARGETS = {
    "mass_not_density": 15,
    "trapped_air": 6,
    "no_causal_model": 6,
    "correct": 3,
}

CATEGORY_BRIEFS = {
    "mass_not_density": (
        "students who think floating is about weight, heaviness, lightness, "
        "or size — anything except density"
    ),
    "trapped_air": (
        "students who think ice floats because it contains or traps air "
        "(bubbles, pockets, balloon-like interior)"
    ),
    "no_causal_model": (
        "students who give no causal explanation — vague appeals to habit or "
        "familiarity ('it just does'), admissions of not knowing, or circular restatements"
    ),
    "correct": (
        "students who correctly reason that ice is less dense than liquid water "
        "(expansion on freezing, mass spread over more volume, displacement)"
    ),
}

GENERATION_PROMPT = """Here are real examples of {category_desc}, answering the question "Why does ice float on water?":

{examples}

Write {n} NEW answers of this same kind. Requirements:
- Same underlying mental model as the examples, but different wording every time.
- Vary sentence structure, length, and voice — these are different 8th graders, some casual, some trying hard to sound scientific.
- Do NOT copy or lightly edit any phrase from the examples or from each other.
- Each answer is one to two sentences, plain text, no quotation marks inside.
- Answers must sound like genuine student writing, including imperfect grammar where natural.

Respond as JSON: {{"answers": ["...", "...", ...]}}"""


def generate_category(
    client: httpx.Client,
    api_key: str,
    model: str,
    expected_cluster: str,
    seed_rows: list[dict],
    count: int,
) -> list[str]:
    examples = "\n".join(f"- {r['response']}" for r in seed_rows)
    prompt = GENERATION_PROMPT.format(
        category_desc=CATEGORY_BRIEFS[expected_cluster],
        examples=examples,
        n=count,
    )
    text = chat_completion(client, api_key, model, prompt, max_tokens=6000)
    payload = parse_json_response(text)
    answers = payload.get("answers")
    if not isinstance(answers, list) or len(answers) != count:
        raise ValueError(
            f"{expected_cluster}: expected {count} answers, got "
            f"{len(answers) if isinstance(answers, list) else type(answers)}"
        )
    cleaned = []
    for a in answers:
        a = str(a).strip().strip('"')
        if not a:
            raise ValueError(f"{expected_cluster}: empty generated answer")
        cleaned.append(a)
    return cleaned


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="regenerate even if output exists")
    parser.add_argument(
        "--out",
        default=str(OUT_FILE),
        help="output path for the expanded dataset (default: demo_data/synthetic_responses_30.json)",
    )
    args = parser.parse_args()
    out_path = Path(args.out)

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    model = os.environ.get("ROOTCAUSE_LLM_MODEL", "stealth/ox-alpha")

    # Resume from partial output if present; otherwise start from the seed.
    if out_path.exists() and not args.refresh:
        expanded = json.loads(out_path.read_text(encoding="utf-8"))
        print(f"Resuming from {out_path} ({len(expanded)} existing rows)")
    else:
        expanded = json.loads(SEED_FILE.read_text(encoding="utf-8"))

    def current_counts() -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in expanded:
            counts[row["expected_cluster"]] = counts.get(row["expected_cluster"], 0) + 1
        return counts

    next_id = max(int(row["student_id"][1:]) for row in expanded) + 1
    with httpx.Client(timeout=180) as client:
        for cluster_name, target_count in CATEGORY_TARGETS.items():
            have = current_counts().get(cluster_name, 0)
            needed = target_count - have
            print(f"{cluster_name}: have {have}, generating {needed} more...")
            if needed <= 0:
                continue
            seed_rows = [
                r
                for r in expanded
                if r["expected_cluster"] == cluster_name
            ]
            answers = generate_category(client, api_key, model, cluster_name, seed_rows, needed)
            for answer in answers:
                expanded.append(
                    {
                        "student_id": f"s{next_id:02d}",
                        "response": answer,
                        "expected_cluster": cluster_name,
                    }
                )
                next_id += 1
            out_path.write_text(
                json.dumps(expanded, indent=2, ensure_ascii=False), encoding="utf-8"
            )

    counts = current_counts()
    print(f"\nWrote {len(expanded)} responses to {out_path}")
    for name, c in sorted(counts.items()):
        print(f"  {name}: {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
