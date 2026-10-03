"""Sentence-transformers wrapper (all-MiniLM-L6-v2 by default)."""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from .config import EMBED_MODEL

_model = None


@lru_cache(maxsize=1)
def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Return an (n, dim) float32 array of normalised embeddings."""
    model = get_model()
    vecs = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return np.asarray(vecs, dtype="float32")


def embed_one(text: str) -> list[float]:
    return embed_texts([text])[0].tolist()
