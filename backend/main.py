"""FastAPI app exposing the RootCause pipeline.

Stages 1-4: extract -> embed -> cluster (+small-cluster merge) -> label.
Optional per-student feedback via include_feedback=true.

Distinct failure signals (per design doc screens 05/06):
- fewer than MIN_RESPONSES responses -> HTTP 422 {"error": "insufficient_responses", ...}
- a successful run where every response lands in noise -> HTTP 200 with a
  single "unclear" cluster card (status "ok")
"""

import os

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from pipeline.cluster import run_stage3
from pipeline.embed import embed_reasoning
from pipeline.extract import ModelUnavailableError, TIMEOUT_SECONDS, extract_batch
from pipeline.label import draft_feedback, run_stage4

MIN_RESPONSES = 8  # design doc screen 06: diagnostics need at least 8

app = FastAPI(title="RootCause", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local dev only until deploy day
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResponseIn(BaseModel):
    student_id: str | None = None
    response: str


class DiagnoseRequest(BaseModel):
    question: str
    correct_concept: str | None = None
    include_feedback: bool = False
    responses: list[ResponseIn] = Field(min_length=1)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/diagnose")
def diagnose(req: DiagnoseRequest) -> dict:
    if len(req.responses) < MIN_RESPONSES:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "insufficient_responses",
                "message": (
                    f"Add a few more responses — diagnostics need at least "
                    f"{MIN_RESPONSES} to find a reliable pattern. This one has {len(req.responses)}."
                ),
                "received": len(req.responses),
                "minimum": MIN_RESPONSES,
            },
        )

    responses = [
        {
            "student_id": r.student_id or f"s{idx + 1:02d}",
            "response": r.response,
        }
        for idx, r in enumerate(req.responses)
    ]

    try:
        records = extract_batch(req.question, responses)
        embeddings = embed_reasoning(records)
        clustering = run_stage3(records, embeddings)
        clusters = run_stage4(req.question, req.correct_concept, records, clustering)

        feedback_by_student: dict[str, str] = {}
        if req.include_feedback:
            api_key = os.environ.get("OPENROUTER_API_KEY", "")
            if not api_key:
                raise RuntimeError("OPENROUTER_API_KEY is not configured")
            by_student = {r["student_id"]: r for r in records}
            misconception_clusters = [c for c in clusters if c["category"] == "misconception"]
            with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
                for cluster in misconception_clusters:
                    for sid in cluster["student_ids"]:
                        rec = by_student[sid]
                        feedback_by_student[sid] = draft_feedback(
                            client,
                            api_key,
                            rec["response_text"],
                            cluster["label"],
                            req.correct_concept or "",
                        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "configuration_error",
                "message": str(exc),
            },
        ) from exc
    except ModelUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "model_unavailable",
                "message": (
                    "The AI providers are busy. RootCause retried MiniMax three times, "
                    "then tried its free fallback. Please try again shortly."
                ),
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "pipeline_error",
                "message": f"Pipeline failed: {exc}",
            },
        ) from exc

    enriched_records = [
        {**r, "feedback_note": feedback_by_student[r["student_id"]]}
        if r["student_id"] in feedback_by_student
        else r
        for r in records
    ]

    return {
        "status": "ok",
        "question": req.question,
        "responses_analyzed": len(records),
        "records": enriched_records,
        "clusters": clusters,
    }
