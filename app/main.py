"""PolarSphere 360 API - FastAPI application entry point."""
from __future__ import annotations

import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import (
    CORS_ORIGINS,
    EMBED_MODEL,
    LLM_BACKEND,
    LLM_MODEL,
    LLM_PRELOAD,
    SERVICE_NAME,
    SERVICE_VERSION,
)
from .db import init_db
from .routers import admin, ai, community, core, outreach, search

app = FastAPI(
    title="PolarSphere 360 API",
    version=SERVICE_VERSION,
    description="Backend for SIH26063 - integrated polar science outreach, knowledge repository and media dissemination portal.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _warm_models() -> None:
    """Load embedding and generator weights in the background.

    Without this the first /api/ai/query pays the full multi-hundred-MB weight
    load and can exceed any sane request timeout.
    """
    try:
        from .embed import get_model

        get_model()
        print("[startup] embedding model ready", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"[startup] embedding warm-up failed: {exc}", flush=True)

    try:
        from .llm import get_generator

        gen = get_generator()
        print(f"[startup] generator ready: {gen.name}", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"[startup] generator warm-up failed: {exc}", flush=True)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    if LLM_PRELOAD == "1":
        threading.Thread(target=_warm_models, daemon=True).start()


@app.get("/health", tags=["meta"])
def health():
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "embeddingModel": EMBED_MODEL,
        "llmBackend": LLM_BACKEND,
        "llmModel": LLM_MODEL,
        "llmPreload": LLM_PRELOAD,
    }


@app.get("/api/contract", tags=["meta"])
def contract():
    """Self-describing endpoint list. Useful for reconciling with the frontend types."""
    routes = []
    for r in app.routes:
        methods = sorted(getattr(r, "methods", []) or [])
        methods = [m for m in methods if m not in ("HEAD", "OPTIONS")]
        if not methods:
            continue
        routes.append({"path": getattr(r, "path", ""), "methods": methods})
    return {"service": SERVICE_NAME, "version": SERVICE_VERSION, "routes": routes}


for _router in (core.router, search.router, ai.router, outreach.router, community.router, admin.router):
    app.include_router(_router)
