"""Shared response envelope and request/response models.

Every endpoint returns {"data": ..., "provenance": {...}} exactly as specified in
docs/backend-integration.md, so the frontend can swap Mock* -> Api* untouched.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


class Citation(BaseModel):
    index: int = 0
    id: str = ""
    title: str = ""
    docType: Optional[str] = None
    station: Optional[str] = None
    year: Optional[int] = None
    snippet: str = ""
    score: Optional[float] = None
    authority: Optional[str] = None
    license: Optional[str] = None


class Provenance(BaseModel):
    source: str = "polarsphere360-api"
    mode: str = "live"  # live | mock | degraded
    generatedAt: str = ""
    latencyMs: Optional[int] = None
    model: Optional[str] = None
    citations: list[Citation] = Field(default_factory=list)
    note: Optional[str] = None


def envelope(
    data: Any,
    *,
    mode: str = "live",
    citations: Optional[list[dict]] = None,
    model: Optional[str] = None,
    note: Optional[str] = None,
    started_at: Optional[float] = None,
    source: str = "polarsphere360-api",
) -> dict:
    """Build the {data, provenance} envelope every route returns."""
    prov = Provenance(
        source=source,
        mode=mode,
        generatedAt=datetime.now(timezone.utc).isoformat(),
        model=model,
        note=note,
        citations=[Citation(**c) if isinstance(c, dict) else c for c in (citations or [])],
    )
    if started_at is not None:
        prov.latencyMs = int((time.perf_counter() - started_at) * 1000)
    return {"data": data, "provenance": prov.model_dump()}


# --------------------------------------------------------------------------
# Requests
# --------------------------------------------------------------------------


class SearchRequest(BaseModel):
    q: str = ""
    type: Optional[str] = None  # documents | datasets | media | all
    docType: Optional[str] = None  # report | paper | dataset-documentation | upload
    station: Optional[str] = None
    theme: Optional[str] = None
    year: Optional[int] = None
    source: Optional[str] = None
    limit: int = 20


class AIQueryRequest(BaseModel):
    q: str
    mode: str = "grounded"  # grounded | summary | compare
    station: Optional[str] = None
    top_k: int = 6


class AnalyticsRequest(BaseModel):
    dataset: str
    op: str = "mean"  # mean | max | min | trend | delta
    range: Optional[str] = None  # e.g. 2015-2025
    station: Optional[str] = None


class OutreachGenerateRequest(BaseModel):
    sourceId: Optional[str] = None
    audience: str = "General Public"
    language: str = "en"
    format: str = "Blog Post"
    tone: Optional[str] = None


class ApproveRequest(BaseModel):
    stage: str
    reviewer: str = "reviewer"


class FieldObservationRequest(BaseModel):
    stationId: Optional[str] = None
    payload: dict = Field(default_factory=dict)


class CitizenAnnotationRequest(BaseModel):
    mediaId: Optional[str] = None
    label: str = ""
    voter: str = "anonymous"


class EntityOut(BaseModel):
    name: str
    kind: str = "concept"
    confidence: float = 0.0
