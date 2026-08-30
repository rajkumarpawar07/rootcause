"""Repopulate the frozen stage-1/stage-4 caches for the recording batch.

Run from backend/ (or anywhere): python populate_cache.py
The first run pays full LLM latency; afterwards the caches are frozen and
reruns are instant. Existing entries are never invalidated — delete keys in
demo_data/*.json to force fresh draws.
"""

import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from pipeline.extract import extract_batch
from pipeline.embed import embed_reasoning
from pipeline.cluster import run_stage3
from pipeline.label import run_stage4

DEMO_DIR = Path(__file__).resolve().parents[1] / "demo_data"
rows = json.loads((DEMO_DIR / "synthetic_responses_30_batchC.json").read_text())
question = 'Why does ice float on water?'
correct_concept = 'Density determines whether an object floats'

print('Stage 1...')
records = extract_batch(question, rows, use_cache=True)
print('Stage 2...')
embeddings = embed_reasoning(records)
print('Stage 3...')
clusters = run_stage3(records, embeddings)

print('Stage 4 (labeling with GLM, then Nemotron fallback if needed)...')
cards = run_stage4(question, correct_concept, records, clusters)
print('Done!')
for c in cards:
    print(f'  [{c["category"]}] {c["label"]} ({c["size"]} · {c["percentage"]}%)')
