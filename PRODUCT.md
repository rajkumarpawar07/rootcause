# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary: K-8 teachers (e.g., the "Ms. Alvarez" persona) with minutes between classes who just collected open-ended answers to one question and need to know what the class misunderstands before teaching tomorrow. Secondary audience for this build: hackathon judges watching a 2-minute demo video (Prometheus August AI Challenge).

## Product Purpose

RootCause reads a batch of open-ended student answers and diagnoses *why* the class got it wrong: an LLM extracts each student's underlying reasoning, embeddings + HDBSCAN cluster shared mental models, and an LLM names each misconception with a concrete reteach suggestion. Success = a teacher looks at one dashboard and knows what to reteach and to whom.

## Positioning

Not a grader or tutor: diagnosis of collective reasoning. Existing AI grading tools speed up per-student feedback; RootCause answers "what does the whole class believe, and where does it diverge from truth?" — embeddings-plus-reasoning pipeline, not a chatbot wrapper.

## Operating Context

Teacher pastes responses into a single form (one response per line), waits seconds-to-minutes while the pipeline runs, then scans a dashboard: stat tiles, a root/branch chart of class shares, cluster cards, drill-in detail with per-student suggested notes. Demo batches are pre-cached so the on-camera run renders in ~3 seconds.

## Capabilities and Constraints

- FastAPI backend at `/api/diagnose` (contract in `frontend/lib/api.ts`); minimum 8 responses else HTTP 422 `insufficient_responses`.
- Six UI states: empty, new-diagnostic form, processing (real stage names), dashboard, cluster detail, too-few.
- Categories map to badges: misconception / solid_understanding / unclear.
- Per-student feedback notes arrive via `include_feedback`; "copy all feedback" in detail view.
- Hard deadline: demo recording by Aug 29; must remain stable end-to-end.
- Accessibility floor from the original spec: text-labeled badges (never color-only), aria-live processing stages, visible focus states, branch-chart text alternative, WCAG AA contrast.

## Brand Commitments

- Name: **RootCause** (fixed).
- The root/branch chart is the signature visual and must survive redesigns.
- Voice: plain, active, specific — never clinical, never judgmental ("Find the patterns", not "Submit").

## Evidence on Hand

- Working end-to-end app (backend + frontend) with locked demo batch `demo_data/synthetic_responses_30_batchC.json`.
- Original design document: `rootcause-design-document.html` (incumbent look being replaced).
- Brief with rubric: `rootcause-project-brief.md`.

## Product Principles

1. Diagnose, don't grade — patterns over verdicts on individual students.
2. Real analysis shown as real analysis — loading states name actual pipeline stages.
3. Calm enough to read between classes — scannable in two minutes.
4. The teacher already knows their kids — surface structure, don't narrate conclusions.

## Accessibility & Inclusion

Never color-only meaning; aria-live progress; keyboard-visible focus rings; chart carries a text summary; AA contrast on both themes used.
