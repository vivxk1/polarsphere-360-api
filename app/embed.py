"""Embeddings. Two backends, selected by EMBED_BACKEND:

  local   - sentence-transformers (all-MiniLM-L6-v2). Default. No API key,
            runs offline, and is what the README describes.
  openai  - hosted embeddings via the OpenAI API. Needs OPENAI_API_KEY.
            Exists so the API can run where torch cannot be installed
            (Vercel's serverless functions cap at 250 MB).

Both backends return L2-normalised float32 vectors, so cosine similarity and
every downstream ranking behave identically whichever one is active.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from .config import (
    EMBED_BACKEND,
    EMBED_DIM,
    EMBED_MODEL,
    EMBED_OPENAI_MODEL,
    OPENAI_API_KEY,
)

_model = None


@lru_cache(maxsize=1)
def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def _normalise(vecs: np.ndarray) -> np.ndarray:
    """L2-normalise rows so dot product == cosine similarity."""
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs / np.clip(norms, 1e-12, None)


def _embed_openai(texts: list[str]) -> np.ndarray:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    out: list[list[float]] = []
    # 96 inputs per request keeps payloads comfortably under the API's limits.
    for i in range(0, len(texts), 96):
        batch = [t.replace("\n", " ").strip() or " " for t in texts[i : i + 96]]
        kwargs = {"model": EMBED_OPENAI_MODEL, "input": batch}
        # Only the text-embedding-3 family accepts a shortened dimension;
        # asking for EMBED_DIM keeps the pgvector column size unchanged.
        if EMBED_OPENAI_MODEL.startswith("text-embedding-3"):
            kwargs["dimensions"] = EMBED_DIM
        resp = client.embeddings.create(**kwargs)
        out.extend([d.embedding for d in resp.data])
    return np.asarray(out, dtype="float32")


def embed_texts(texts: list[str]) -> np.ndarray:
    """Return an (n, dim) float32 array of normalised embeddings."""
    if not texts:
        return np.zeros((0, EMBED_DIM), dtype="float32")

    if EMBED_BACKEND.lower() == "openai" and OPENAI_API_KEY:
        return _normalise(_embed_openai(texts))

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
