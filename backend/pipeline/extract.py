"""Stage 1 — reasoning extraction.

One LLM call per response: describe the mental model behind the answer,
never judge correctness. Prompt is verbatim from section 5 of the brief.

LLM transport: OpenRouter (OpenAI-compatible chat completions), with
`minimax/minimax-m3:free` as the preferred model and a controlled free fallback.
"""

import hashlib
import json
import os
import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

SYSTEM_PROMPT = (
    "You are analyzing a student's answer to identify the reasoning "
    "behind it, not to judge whether it's correct."
)

USER_PROMPT_TEMPLATE = """Question: {question_text}
Student answer: {student_answer}

In one or two sentences, describe the mental model or reasoning the
student is using to arrive at this answer — even if the answer happens
to be correct. Do not evaluate correctness. Focus only on the underlying
logic.
{brevity_clause}
Respond as JSON: {{"reasoning_summary": "..."}}"""

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "minimax/minimax-m3:free"
FALLBACK_OPENROUTER_MODEL = "nvidia/nemotron-3.5-lightning:free"
PRIMARY_MODEL_ATTEMPTS = 3
FALLBACK_MODEL_ATTEMPTS = 3
TIMEOUT_SECONDS = 60

STAGE1_CACHE = Path(__file__).resolve().parents[2] / "demo_data" / "stage1_cache.json"


def _cache_key(question_text: str, response: str) -> str:
    limit = summary_word_limit()
    suffix = f"||limit={limit}" if limit > 0 else ""
    return hashlib.sha256(f"{question_text}||{response}{suffix}".encode("utf-8")).hexdigest()


def _load_cache() -> dict:
    if STAGE1_CACHE.exists():
        try:
            return json.loads(STAGE1_CACHE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    STAGE1_CACHE.parent.mkdir(parents=True, exist_ok=True)
    STAGE1_CACHE.write_text(
        json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def parse_json_response(text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1:
        missing = "opening" if start == -1 else "closing"
        raise ValueError(
            f"JSON response missing {missing} brace (likely token-truncated): {text[:200]}"
        )
    parsed = json.loads(cleaned[start : end + 1])
    if not parsed:
        raise ValueError(f"Empty JSON object from LLM: {text[:200]}")
    if "reasoning_summary" not in parsed:
        first_val = next(iter(parsed.values()), None)
        if isinstance(first_val, str) and first_val:
            parsed["reasoning_summary"] = first_val
        else:
            raise ValueError(f"Missing reasoning_summary in LLM response: {text[:200]}")
    return parsed


class ModelUnavailableError(RuntimeError):
    """Both OpenRouter model paths were unavailable after their retry budgets."""


def _request_completion(
    client: httpx.Client,
    api_key: str,
    model: str,
    user_prompt: str,
    max_tokens: int,
    temperature: float,
) -> str:
    resp = client.post(
        OPENROUTER_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        },
    )
    resp.raise_for_status()
    payload = resp.json()
    choices = payload.get("choices") or []
    if not choices:
        raise ValueError(f"OpenRouter returned no choices: {str(payload)[:200]}")
    message = choices[0].get("message") or {}
    content = str(message.get("content") or "").strip()
    if not content:
        finish_reason = choices[0].get("finish_reason")
        raise ValueError(
            f"Empty content (finish_reason={finish_reason}): {str(payload)[:200]}"
        )
    return content


def chat_completion(
    client: httpx.Client,
    api_key: str,
    user_prompt: str,
    max_tokens: int = 1500,
    parse: Callable[[str], Any] | None = None,
) -> Any:
    """Request a completion (optionally parsed) under the retry/fallback budget.

    When `parse` is given it runs inside the retry loop, so a 200 response
    whose body fails to parse (truncated JSON, prose instead of JSON, ...)
    consumes an attempt and can trigger the model fallback instead of
    escaping as an unhandled ValueError."""
    # Low temperature by default: stage-1 summary drift between identical
    # requests measured mean cosine 0.88 run-to-run, which churns cluster
    # boundaries downstream (purity swung 0.40 -> 0.57 on the same config).
    try:
        temperature = float(os.environ.get("ROOTCAUSE_LLM_TEMPERATURE", "0.2"))
    except ValueError:
        temperature = 0.2
    # A rate-limited preferred model gets exactly three attempts before the
    # pipeline switches to its declared fallback. Keeping the policy here,
    # rather than at every stage, prevents nested retry loops from turning a
    # three-attempt policy into dozens of requests.
    last_error: Exception | None = None
    model_attempts = (
        (OPENROUTER_MODEL, PRIMARY_MODEL_ATTEMPTS),
        (FALLBACK_OPENROUTER_MODEL, FALLBACK_MODEL_ATTEMPTS),
    )
    for model_index, (model, attempts) in enumerate(model_attempts):
        budget = max_tokens
        for attempt in range(attempts):
            try:
                content = _request_completion(
                    client, api_key, model, user_prompt, budget, temperature
                )
                return parse(content) if parse else content
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                if attempt + 1 < attempts:
                    if isinstance(exc, ValueError) and "finish_reason=length" in str(exc):
                        budget = min(budget * 2, 32000)
                    delay = attempt + 1
                    print(f"  {model} failed; retrying in {delay}s ({attempt + 1}/{attempts})...")
                    time.sleep(delay)
        if model_index == 0:
            print(
                f"  {OPENROUTER_MODEL} failed after {PRIMARY_MODEL_ATTEMPTS} attempts; "
                f"trying fallback {FALLBACK_OPENROUTER_MODEL}..."
            )
    raise ModelUnavailableError(
        "Both OpenRouter models were unavailable after retrying: "
        f"{OPENROUTER_MODEL} ({PRIMARY_MODEL_ATTEMPTS} attempts), then "
        f"{FALLBACK_OPENROUTER_MODEL} ({FALLBACK_MODEL_ATTEMPTS} attempts)."
    ) from last_error


def summary_word_limit() -> int:
    """Optional cap on summary length. 0 (default) = uncapped.

    Experimented with a hard 20-word cap: compressed summaries clustered
    WORSE on both the seed set and the expanded set (verbose wins — the
    extra interpretive detail is discriminative signal). Knob kept for
    future experiments only.
    """
    return int(os.environ.get("ROOTCAUSE_SUMMARY_WORD_LIMIT", "0"))


def build_user_prompt(question_text: str, student_answer: str) -> str:
    limit = summary_word_limit()
    brevity_clause = (
        f"\nHard limit: at most {limit} words. No preamble, no analysis — just\nthe summary itself.\n"
        if limit > 0
        else ""
    )
    return USER_PROMPT_TEMPLATE.format(
        question_text=question_text,
        student_answer=student_answer,
        brevity_clause=brevity_clause,
    )


def extract_reasoning(
    client: httpx.Client, api_key: str, question_text: str, student_answer: str
) -> str:
    prompt = build_user_prompt(question_text, student_answer)
    parsed = chat_completion(
        client,
        api_key,
        prompt,
        max_tokens=1000,
        parse=parse_json_response,
    )
    summary = parsed.get("reasoning_summary", "").strip()
    if not summary:
        raise ValueError("Empty reasoning_summary in LLM response")
    return summary


def extract_batch(
    question_text: str,
    responses: list[dict],
    use_cache: bool = True,
) -> list[dict]:
    """Run stage 1 over every response.

    Input items: {"student_id": str, "response": str}
    Output items (schema per brief section 5):
        {"student_id": str, "response_text": str, "reasoning_summary": str}

    Read-through cache keyed on (question, response, word-limit): identical
    responses return their stored summary instead of a fresh LLM draw. This
    makes a validated demo batch reproduce its exact dashboard on camera —
    stage-1 drift between draws otherwise swings cluster structure.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set — stage 1 needs it for reasoning extraction"
        )
    cache = _load_cache() if use_cache else {}
    results: list[dict] = []
    misses: list[dict] = []
    for item in responses:
        key = _cache_key(question_text, item["response"])
        if key in cache and use_cache:
            results.append(
                {
                    "student_id": item["student_id"],
                    "response_text": item["response"],
                    "reasoning_summary": cache[key],
                }
            )
        else:
            misses.append(item)

    if misses:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            for item in misses:
                answer = item["response"]
                summary = extract_reasoning(client, api_key, question_text, answer)
                cache[_cache_key(question_text, answer)] = summary
                results.append(
                    {
                        "student_id": item["student_id"],
                        "response_text": answer,
                        "reasoning_summary": summary,
                    }
                )
        if use_cache:
            _save_cache(cache)
    return results
