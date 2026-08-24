"""Stage 4 — cluster labeling + reteach suggestions (+ optional per-student notes).

Per-cluster prompt is verbatim from section 5 of the brief, with one
addition: the JSON response carries a `category` field so each cluster can
render the correct badge (Misconception / Solid understanding / Unclear)
per the design document's accessibility rules. Noise clusters skip the LLM
entirely — there is no coherent reasoning to name — and render as a fixed
"unclear" card.
"""

import hashlib
import json
import os
import re
from pathlib import Path

import httpx
from dotenv import load_dotenv

from .extract import chat_completion, parse_json_response

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

STAGE4_CACHE = Path(__file__).resolve().parents[2] / "demo_data" / "stage4_cache.json"


def _stage4_cache_key(
    question_text: str,
    correct_concept: str,
    members: list[tuple[str, str]],
) -> str:
    """members: [(student_id, reasoning_summary)] — order-sensitive by design."""
    payload = json.dumps(
        {
            "q": question_text,
            "c": correct_concept or "",
            "m": [[sid, s] for sid, s in members],
        },
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_stage4_cache() -> dict:
    if STAGE4_CACHE.exists():
        try:
            return json.loads(STAGE4_CACHE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_stage4_cache(cache: dict) -> None:
    STAGE4_CACHE.write_text(
        json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8"
    )

STAGE4_SYSTEM_PROMPT = (
    "You are an experienced teacher analyzing a group of students "
    "who reasoned about a concept in a similar way."
)

STAGE4_USER_TEMPLATE = """Question: {question_text}
Correct concept: {correct_concept}

Here are {n} students' reasoning summaries, grouped together because
they are semantically similar:
{list_of_reasoning_summaries}

1. Name this shared mental model in plain, teacher-friendly language
   (5-8 words).
2. In one sentence, explain the gap between this reasoning and the
   correct concept.
3. Suggest one concrete, concise reteach activity (1-2 sentences) that
   directly addresses this specific misconception.

Respond as JSON:
{{"label": "...", "gap": "...", "reteach_suggestion": "...", "category": "...", "solid_member_positions": []}}"""

CATEGORY_INSTRUCTION = (
    '\nFor "category", classify the shared mental model as exactly one of:\n'
    '- "misconception": the students share a flawed model that conflicts\n'
    "  with the correct concept\n"
    '- "solid_understanding": the students reason correctly about the\n'
    "  concept (their answers align with the correct concept)\n"
    "\n"
    'For "solid_member_positions": clustering groups students by similar\n'
    "wording, so sometimes a student who reasons CORRECTLY lands inside a\n"
    "misconception group. List the position numbers (1-{n}, matching the\n"
    "numbered summaries above) of any listed students whose reasoning\n"
    "aligns with the correct concept. If none, return an empty list.\n"
)

SOLID_CARD_LABEL = "Correct reasoning"
SOLID_CARD_RETEACH = (
    "No reteach needed — invite one of these students to explain their "
    "thinking during the lesson so peers hear a correct model in "
    "classmate language."
)

FEEDBACK_SYSTEM_PROMPT = (
    "You write short, encouraging feedback for students. You never shame "
    "a student for their reasoning."
)

# Verbatim from section 5 of the brief (optional personalized feedback).
FEEDBACK_USER_TEMPLATE = """Student answer: {student_answer}
Identified misconception: {cluster_label}
Correct concept: {correct_concept}

Write short (2-3 sentence), encouraging feedback directly to the
student. Acknowledge what's reasonable in their thinking, name the
specific gap without being discouraging, and point them toward the
correct idea. Do not simply say "incorrect"."""


UNCLEAR_CARD = {
    "label": "No causal model yet",
    "gap": "",
    "reteach_suggestion": (
        "Reteach with a concrete demonstration first: predict, then test, "
        "which everyday objects sink or float, and ask students to explain "
        "each result before introducing the target concept."
    ),
    "category": "unclear",
}

MAX_REPRESENTATIVE_SUMMARIES = 12

VALID_CATEGORIES = {"misconception", "solid_understanding", "unclear"}


def _representative_summaries(summaries: list[str], limit: int = MAX_REPRESENTATIVE_SUMMARIES) -> list[tuple[int, str]]:
    """Deterministic even sampling: returns [(member_index, summary), ...]."""
    if len(summaries) <= limit:
        return list(enumerate(summaries))
    step = len(summaries) / limit
    indices = sorted({min(len(summaries) - 1, int(i * step)) for i in range(limit)})
    return [(i, summaries[i]) for i in indices]


def _strip_fields(payload: dict) -> tuple[dict, str, list[int]]:
    category = str(payload.get("category", "misconception")).strip().lower()
    if category not in VALID_CATEGORIES:
        category = "misconception"
    raw_positions = payload.get("solid_member_positions", [])
    positions = []
    if isinstance(raw_positions, list):
        for p in raw_positions:
            try:
                pos = int(p)
            except (TypeError, ValueError):
                continue
            if 1 <= pos <= MAX_REPRESENTATIVE_SUMMARIES:
                positions.append(pos - 1)  # store 0-based
    payload.pop("category", None)
    payload.pop("solid_member_positions", None)
    return payload, category, sorted(set(positions))


def label_cluster(
    client: httpx.Client,
    api_key: str,
    question_text: str,
    correct_concept: str,
    members: list[tuple[int, str]],
) -> dict:
    listed = "\n".join(f"- {s}" for _, s in members)
    prompt = (
        STAGE4_USER_TEMPLATE.format(
            question_text=question_text,
            correct_concept=correct_concept or "(not provided)",
            n=len(members),
            list_of_reasoning_summaries=listed,
        )
        + CATEGORY_INSTRUCTION.format(n=len(members))
    )
    # Generous token budget: stealth/ox-alpha spends hidden reasoning tokens
    # before emitting any content, and long gap/reteach text can push the
    # JSON past smaller budgets mid-object.
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            text = chat_completion(
                client,
                api_key,
                os.environ.get("ROOTCAUSE_LLM_MODEL", "stealth/ox-alpha"),
                prompt,
                max_tokens=6000,
            )
            payload, category, solid_positions = _strip_fields(parse_json_response(text))
            return {
                "label": str(payload.get("label", "")).strip() or "Shared reasoning pattern",
                "gap": str(payload.get("gap", "")).strip(),
                "reteach_suggestion": str(payload.get("reteach_suggestion", "")).strip(),
                "category": category,
                "_solid_positions": solid_positions,
            }
        except Exception as exc:  # truncation/parse/transient -> retry
            last_error = exc
    raise RuntimeError(f"Stage 4 labeling failed after retries: {last_error}")


def draft_feedback(
    client: httpx.Client,
    api_key: str,
    student_answer: str,
    cluster_label: str,
    correct_concept: str,
) -> str:
    prompt = FEEDBACK_USER_TEMPLATE.format(
        student_answer=student_answer,
        cluster_label=cluster_label,
        correct_concept=correct_concept or "(not provided)",
    )
    text = chat_completion(
        client,
        api_key,
        os.environ.get("ROOTCAUSE_LLM_MODEL", "stealth/ox-alpha"),
        prompt,
        max_tokens=6000,  # reasoning model: leave room for hidden reasoning
    )
    note = text.strip()
    if note.startswith('"') and note.endswith('"'):
        note = note[1:-1]
    return re.sub(r"^Feedback:\s*", "", note, flags=re.IGNORECASE)


def run_stage4(
    question_text: str,
    correct_concept: str | None,
    records: list[dict],
    clustering,
) -> list[dict]:
    """Label every cluster in the stage-3 output and audit for correct reasoners.

    Each labeled cluster may have members flagged (via the same LLM call) as
    actually matching the correct concept; flagged members from all clusters
    consolidate into a single "Correct reasoning" card with category
    "solid_understanding" — per the design doc, that group is its own slice,
    never merged into Unclear.

    Returns cluster dicts extended with {label, gap, reteach_suggestion,
    category, size, student_ids, percentage, example_response} (schema per
    brief section 5, after stage 4). Noise clusters get the fixed unclear
    card without an LLM call. Per-cluster labels are served from and written
    back to demo_data/stage4_cache.json so a validated batch reproduces its
    exact cards.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set — stage 4 needs it")

    by_student = {r["student_id"]: r for r in records}
    cards: list[dict] = []
    solid_members: list[dict] = []
    cache = _load_stage4_cache()
    cache_dirty = False

    with httpx.Client(timeout=120) as client:
        for cluster in clustering.clusters:
            members = [by_student[sid] for sid in cluster["student_ids"]]
            if cluster["cluster_id"] == -1 or not members:
                card = dict(cluster)
                card.update(UNCLEAR_CARD)
                card["_members"] = members
                cards.append(card)
                continue

            reps = _representative_summaries([m["reasoning_summary"] for m in members])
            key = _stage4_cache_key(
                question_text,
                correct_concept or "",
                [(members[i]["student_id"], s) for i, s in reps],
            )
            if key in cache:
                labeled = dict(cache[key])
                solid_positions = labeled.pop("_solid_positions", [])
            else:
                labeled = label_cluster(
                    client, api_key, question_text, correct_concept or "", reps
                )
                solid_positions = labeled.pop("_solid_positions", [])
                cache[key] = {**labeled, "_solid_positions": solid_positions}
                cache_dirty = True

            flagged_ids = {members[i]["student_id"] for i in solid_positions if i < len(members)}

            if flagged_ids:
                remaining = [m for m in members if m["student_id"] not in flagged_ids]
                solid_members.extend(m for m in members if m["student_id"] in flagged_ids)
                if remaining:
                    card = dict(cluster)
                    card.update(labeled)
                    card["student_ids"] = [m["student_id"] for m in remaining]
                    card["_members"] = remaining
                    cards.append(card)
            else:
                card = dict(cluster)
                card.update(labeled)
                if labeled["category"] == "solid_understanding":
                    # Whole group is solid — fold into the single correct card.
                    solid_members.extend(members)
                else:
                    card["_members"] = members
                    cards.append(card)

    if cache_dirty:
        _save_stage4_cache(cache)

    if solid_members:
        cards.append(
            {
                "cluster_id": max((c["cluster_id"] for c in cards), default=0) + 1,
                "label": SOLID_CARD_LABEL,
                "gap": "",
                "reteach_suggestion": SOLID_CARD_RETEACH,
                "category": "solid_understanding",
                "student_ids": [m["student_id"] for m in solid_members],
                "_members": solid_members,
            }
        )

    total = sum(len(c["_members"]) for c in cards) or 1
    final: list[dict] = []
    for c in sorted(cards, key=lambda c: c.get("category") == "unclear"):
        members = c["_members"]
        final.append(
            {
                "cluster_id": int(c["cluster_id"]),
                "label": c["label"],
                "gap": c["gap"],
                "reteach_suggestion": c["reteach_suggestion"],
                "category": c["category"],
                "size": len(members),
                "percentage": round(len(members) / total * 100),
                "example_response": members[0]["response_text"] if members else "",
                "student_ids": [m["student_id"] for m in members],
            }
        )
    return final
