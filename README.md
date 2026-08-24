# RootCause

An AI misconception-diagnosis tool for teachers — built for the Prometheus August AI Challenge.
See `rootcause-project-brief.md` for the full spec and `rootcause-design-document.html` for the visual system.

## Status

Day 4 complete: dashboard UI built to the design document spec (screens 01–06), talking to the live API. Full dress rehearsal passed on the recording batch (`demo_data/synthetic_responses_30_batchC.json`): six cards, correct-reasoning trio intact in its own Solid-understanding slice.

**Validation results** (`python -m pipeline.validate`):

| Dataset | Purity | Notes |
|---|---|---|
| §9 seed set (15) | **0.53 – 0.80 across summary draws** | stage-1 nondeterminism moves this; see findings |
| Expanded set (30, generated from seed) | 0.40 – 0.57 | same effect |

*Findings:*
- **Stage-1 summaries drift between runs** (mean cosine 0.88 across identical re-extractions). Measured impact: the same fixed config scores 0.53 or 0.80 on the seed set depending only on which draw is cached. Mitigations shipped: sampling temperature defaults to 0.2 (`ROOTCAUSE_LLM_TEMPERATURE`), plus read-through caches (below).
- HDBSCAN alone never isolates the correct-reasoning trio at n=30 (verified over 5 draws). Stage 4 audits each cluster's members in the same labeling call and consolidates correct reasoners into one "Correct reasoning" card.
- Embedding raw response concatenated with its reasoning summary beats summary-only on small batches; current default: concat + PCA(6) + HDBSCAN(cosine, mcs=3). Verbose summaries beat compressed ones (`ROOTCAUSE_SUMMARY_WORD_LIMIT` stays off).
- Clusters below ~10% of the batch merge into their nearest neighbor pre-labeling.

## Demo determinism (important)

Stage 1 and stage 4 both use read-through caches (`demo_data/stage1_cache.json`, `demo_data/stage4_cache.json`). The FIRST run of a given batch pays full LLM latency (~18 min at n=30 with feedback on the free tier); every rerun returns identical cards in ~3 seconds because clusters and labels are served frozen. Per-student feedback notes are always drafted live.

Demo-day workflow: run batch C once ahead of time (done — locked), then paste it on camera; the dashboard renders in seconds. Delete a cache file to force fresh LLM draws.

## Run the app

Backend (terminal 1):
```powershell
cd backend
..\ .venv\Scripts\Activate.ps1   # or use .venv\Scripts\python.exe directly
uvicorn main:app --port 8000
```

Frontend (terminal 2):
```powershell
cd frontend
npm run dev    # http://localhost:3000
```

Set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` to point anywhere other than `http://localhost:8000`.

## Stage 4 & API behavior

- Each cluster becomes a dashboard card: `{label, gap, reteach_suggestion, category, size, percentage, example_response}`. Categories map to the design doc's badges: `misconception` (gold), `solid_understanding` (moss), `unclear` (muted).
- Noise responses become one fixed **Unclear** card ("No causal model yet") without an LLM call.
- `POST /api/diagnose` rejects batches under 8 responses with HTTP 422 `{error: "insufficient_responses", received, minimum}` — a distinct signal from a successful all-unclear run (HTTP 200).
- Add `"include_feedback": true` to also draft a personalized 2–3 sentence note per student in misconception clusters (`feedback_note` on each record).

## Structure

```
backend/
  main.py                 # FastAPI app
  pipeline/
    extract.py            # stage 1 — reasoning extraction (OpenRouter)
    embed.py              # stage 2 — all-MiniLM-L6-v2 embeddings
    cluster.py            # stage 3 — HDBSCAN + small-cluster merge
    label.py              # stage 4 — labeling, reteach, per-student notes
    generate_data.py      # grows the seed into full demo batches
    validate.py           # checks cluster output vs expected_cluster labels
  requirements.txt
frontend/
  app/                    # Next.js dashboard (design doc screens 01-06)
  lib/api.ts              # typed API client
demo_data/
  synthetic_responses.json            # section-9 seed set
  synthetic_responses_30_batch*.json  # generated demo batches (C = recording)
  stage1_cache.json                   # frozen reasoning summaries (demo determinism)
  stage4_cache.json                   # frozen cluster labels/audits
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

Stage 1 uses OpenRouter (model `stealth/ox-alpha` by default). Put `OPENROUTER_API_KEY=...` in a `.env` file at the repo root (already gitignored); override the model with `ROOTCAUSE_LLM_MODEL`.

## Validate the pipeline

```powershell
cd backend
python -m pipeline.validate              # full pipeline incl. LLM stage 1
python -m pipeline.validate --skip-extract   # embed raw text, no API calls
python -m pipeline.validate --dataset ..\demo_data\synthetic_responses_30.json   # expanded set
python -m pipeline.validate --with-labels    # also run stage 4 and print dashboard cards
```

Reports purity / ARI against the `expected_cluster` labels. Stage-1 summaries are cached in `demo_data/stage1_cache.json`, so repeat runs skip the LLM.

## Generate demo data

```powershell
cd backend
python -m pipeline.generate_data         # grows the seed to 30 rows (resumable)
```

## Run the API

```powershell
cd backend
uvicorn main:app --reload
```

- `GET /health`
- `POST /api/diagnose` — `{question, correct_concept?, responses:[{student_id?, response}]}` → reasoning summaries per student + clusters
