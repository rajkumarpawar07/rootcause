import json
import os
from pathlib import Path

os.environ['OPENROUTER_API_KEY'] = os.environ.get('OPENROUTER_API_KEY', '')
os.environ['ROOTCAUSE_LLM_MODEL'] = 'nvidia/nemotron-3-ultra-550b-a55b:free'
os.environ['ROOTCAUSE_LLM_TEMPERATURE'] = '0.2'

from pipeline.extract import extract_batch
from pipeline.embed import embed_reasoning
from pipeline.cluster import run_stage3
from pipeline.label import run_stage4

rows = json.loads(Path('../demo_data/synthetic_responses_30_batchC.json').read_text())
question = 'Why does ice float on water?'
correct_concept = 'Density determines whether an object floats'

print('Stage 1...')
summaries = extract_batch(question, rows, use_cache=True)
print('Stage 2...')
embeddings = embed_reasoning(summaries)
print('Stage 3...')
clusters = run_stage3(summaries, embeddings)
print('Stage 4 (labeling with nemotron)...')
cards = run_stage4(question, correct_concept, summaries, clusters)
print('Done!')
for c in cards:
    print(f'  [{c["category"]}] {c["label"]} ({c["size"]} · {c["percentage"]}%)')