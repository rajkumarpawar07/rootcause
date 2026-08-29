"""Stage 4 — cluster labeling + reteach suggestions (+ optional per-student notes).

Per-cluster prompt is verbatim from section 5 of the brief, with one
addition: the JSON response carries a `category` field so each cluster can
render the correct badge (Misconception / Solid understanding / Unclear)
per the design document's accessibility rules. Noise clusters skip the LLM
entirely — there is no coherent reasoning to name — and render as a fixed
"unclear" card.

Solid-promotion guard: the in-band `solid_member_positions` audit runs
inside group context and over-flags students who merely borrow correct
vocabulary (measured on batch C: 3 of 6 promoted members held flawed
models). Every individually flagged member therefore faces a second,
isolated yes/no verification against the correct concept before joining
the "Correct reasoning" card. Verified verdicts are cached alongside the
cluster labels (distinct keys), so existing label caches stay valid.
Requires a non-empty correct_concept; without one, audit flags are
trusted as-is (nothing to verify against).
"""

import hashlib
import json
import os
import re
from pathlib import Path

import httpx
import numpy as np
from dotenv import load_dotenv

from .embed import embed_texts
from .extract import chat_completion, parse_json_response

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

STAGE4_CACHE = Path(__file__).resolve().parents[2] / "demo_data" / "stage4_cache.json"

DEFAULT_LLM_MODEL = "stealth/ox-alpha"


def _stage4_cache_key(
    question_text: str,
    correct_concept: str,
    members: list[tuple[str, str]],
    model: str,
) -> str:
    """members: [(student_id, reasoning_summary)] — order-sensitive by design."""
    payload = json.dumps(
        {
            "q": question_text,
            "c": correct_concept or "",
            "m": [[sid, s] for sid, s in members],
            "model": model,
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


def _verify_cache_key(
    question_text: str,
    correct_concept: str,
    student_id: str,
    response_text: str,
    reasoning_summary: str,
) -> str:
    payload = json.dumps(
        {
            # Version bump whenever VERIFY_USER_TEMPLATE's semantics change
            # or the verdict rule changes (v4: rubric judges the student's
            # own theory; displaced-water weight explicitly blessed), so
            # stale verdicts from an older rubric are never served.
            "kind": "verify.v4",
            "q": question_text,
            "c": correct_concept,
            "sid": student_id,
            "r": response_text,
            "s": reasoning_summary,
        },
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_supports_concept(
    client: httpx.Client,
    api_key: str,
    cache: dict,
    question_text: str,
    correct_concept: str,
    member: dict,
) -> bool:
    """Second-layer check: does this student's causal model actually match
    the correct concept?

    Single draws proved unstable under rate-limit retries (one redrawing
    judged the batch's most textbook-correct answer as unsupported), so
    the rubric is applied VERIFY_VOTES times and a strict majority of
    valid votes decides; the winning verdict plus the individual votes
    are cached. With zero valid votes the audit flag is trusted (old
    behavior) rather than blocking the pipeline."""
    key = _verify_cache_key(
        question_text,
        correct_concept,
        member["student_id"],
        member["response_text"],
        member["reasoning_summary"],
    )
    if key in cache:
        return bool(cache[key].get("supports_correct_concept"))
    prompt = VERIFY_USER_TEMPLATE.format(
        question_text=question_text,
        correct_concept=correct_concept or "(not provided)",
        student_answer=member["response_text"],
        reasoning_summary=member["reasoning_summary"],
    )
    votes: list[bool] = []
    last_error: Exception | None = None
    for _ in range(VERIFY_VOTES):
        try:
            text = chat_completion(
                client,
                api_key,
                os.environ.get("ROOTCAUSE_LLM_MODEL", DEFAULT_LLM_MODEL),
                prompt,
                max_tokens=4000,
            )
            votes.append(
                bool(parse_json_response(text).get("supports_correct_concept"))
            )
        except Exception as exc:
            last_error = exc
    if not votes:
        print(f"  verify failed for {member['student_id']}, trusting audit flag: {last_error}")
        return True
    verdict = sum(votes) * 2 > len(votes)
    cache[key] = {"supports_correct_concept": verdict, "votes": votes}
    return verdict

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

VERIFY_SYSTEM_PROMPT = (
    "You are fact-checking whether one student's reasoning truly matches "
    "the correct concept, or merely sounds scientific."
)

# Encodes the project's ground-truth policy (brief section 9): weight /
# lightness / size framings ARE the target misconception even when the
# statement is numerically true ("ice weighs less than the same-size
# chunk of water"), and trapped-air mechanisms are a separate
# misconception, not the correct concept. Without this rubric the judge
# model passes informal-weight answers as "implicitly density". The
# student's OWN theory of why ice floats is what's judged — Archimedes'
# displaced-water weight is part of the correct density story and must
# not trip the weight clause (measured: it did, unanimously, until the
# clause targeted the student's theory rather than any mention of
# weight).
VERIFY_USER_TEMPLATE = """Question: {question_text}
Correct concept: {correct_concept}

Student answer: {student_answer}
Extracted reasoning: {reasoning_summary}

Does this student's causal explanation align with the correct concept?
Judge the student's OWN theory of WHY ice floats, applying this rubric:

- SUPPORTS the concept if their theory hinges on density — how much mass
  is packed into a given volume, ice being less dense than liquid water,
  or freezing spreading the molecules apart so the same mass occupies
  more space. Mentioning the weight of DISPLACED WATER is part of this
  density story and still supports the concept.
- Does NOT support it if their theory is that ice itself is lighter or
  less heavy than water (rather than less dense per unit volume), or
  that being small / pulled down gently keeps it up — even when
  comparing equal sizes and even if the claim is numerically true.
- Does NOT support it if floating is attributed to incidental features
  (trapped air pockets, gas bubbles, hollow spots) instead of how the
  substance's own molecules are arranged.

Respond as JSON: {{\"supports_correct_concept\": true}}
or {{\"supports_correct_concept\": false}}"""

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

VERIFY_VOTES = 3  # self-consistency votes per verified member (majority wins)

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
                os.environ.get("ROOTCAUSE_LLM_MODEL", DEFAULT_LLM_MODEL),
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
        os.environ.get("ROOTCAUSE_LLM_MODEL", DEFAULT_LLM_MODEL),
        prompt,
        max_tokens=6000,  # reasoning model: leave room for hidden reasoning
    )
    note = text.strip()
    if note.startswith('"') and note.endswith('"'):
        note = note[1:-1]
    return re.sub(r"^Feedback:\s*", "", note, flags=re.IGNORECASE)


def _pick_solid_example(members: list[dict], correct_concept: str | None) -> str:
    """Deterministic on-camera exemplar for the "Correct reasoning" card:
    the member whose reasoning summary sits closest to the correct concept.
    (members[0] can be a borderline answer that clustered alongside solid
    reasoners — measured on batch C, where it surfaced a weight-based
    response under a Solid-understanding badge.) Falls back to the first
    member when no concept was provided.
    """
    if not members:
        return ""
    if len(members) == 1 or not (correct_concept or "").strip():
        return members[0]["response_text"]
    vecs = embed_texts([correct_concept] + [m["reasoning_summary"] for m in members])
    normed = vecs / (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9)
    sims = normed[1:] @ normed[0]
    best = max(range(len(members)), key=lambda i: (float(sims[i]), -i))
    return members[best]["response_text"]


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
            model = os.environ.get("ROOTCAUSE_LLM_MODEL", DEFAULT_LLM_MODEL)
            key = _stage4_cache_key(
                question_text,
                correct_concept or "",
                [(members[i]["student_id"], s) for i, s in reps],
                model,
            )
            # backward compat: try old key (without model) if new key not found
            if key not in cache:
                old_key = _stage4_cache_key(
                    question_text,
                    correct_concept or "",
                    [(members[i]["student_id"], s) for i, s in reps],
                    "",
                )
                if old_key in cache:
                    key = old_key
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

            # Solid-promotion guard: audit flags from misconception groups
            # face an isolated verification before joining the solid card.
            if flagged_ids and (correct_concept or "").strip():
                verified: set[str] = set()
                for m in members:
                    if m["student_id"] not in flagged_ids:
                        continue
                    before = len(cache)
                    ok = verify_supports_concept(
                        client, api_key, cache, question_text,
                        correct_concept or "", m,
                    )
                    if len(cache) != before:
                        cache_dirty = True
                    if ok:
                        verified.add(m["student_id"])
                flagged_ids = verified

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
                "_example": _pick_solid_example(solid_members, correct_concept),
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
                "example_response": c.get("_example") or (members[0]["response_text"] if members else ""),
                "student_ids": [m["student_id"] for m in members],
            }
        )
    return final
