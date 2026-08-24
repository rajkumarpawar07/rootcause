"""Stage 2 — embedding.

Embed each reasoning summary with all-MiniLM-L6-v2 via sentence-transformers.
Local, free, no extra API key (brief section 6).
"""

import os

import numpy as np

DEFAULT_MODEL = "all-MiniLM-L6-v2"

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(os.environ.get("ROOTCAUSE_EMBED_MODEL", DEFAULT_MODEL))
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Return an (n, d) float32 matrix of embeddings, one row per text."""
    if not texts:
        return np.empty((0, 384), dtype=np.float32)
    model = _get_model()
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=False)
    return np.asarray(embeddings, dtype=np.float32)


def embed_reasoning(records: list[dict], include_response_text: bool = True) -> np.ndarray:
    """Embed each stage-1 record for clustering.

    Empirically (see repo history), embedding the raw response concatenated
    with its reasoning summary separates misconceptions far better than
    either alone: the response contributes concrete surface anchors, the
    summary contributes the inferred logic underneath paraphrase.
    """
    if include_response_text:
        texts = [f"{r['response_text']}\n{r['reasoning_summary']}" for r in records]
    else:
        texts = [r["reasoning_summary"] for r in records]
    return embed_texts(texts)
