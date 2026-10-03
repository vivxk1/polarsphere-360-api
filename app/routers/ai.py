"""Polar AI: grounded RAG answers and dataset analytics."""
from __future__ import annotations

import time

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Dataset, DatasetPoint
from ..rag import answer_question
from ..schemas import AIQueryRequest, AnalyticsRequest, envelope
from ..llm import get_generator

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/query")
def ai_query(req: AIQueryRequest, db: Session = Depends(get_db)):
    t0 = time.perf_counter()
    if not req.q.strip():
        raise HTTPException(400, "q must not be empty")

    result = answer_question(db, req.q, mode=req.mode, station=req.station, top_k=req.top_k)

    gen = get_generator()
    result["steps"] = [
        {"step": "query_embedded", "status": "done"},
        {"step": "vector_search", "status": "done"},
        {"step": "fulltext_search", "status": "done"},
        {"step": "reciprocal_rank_fusion", "status": "done"},
        {"step": "generate_with_citations", "status": "done"},
    ]
    return envelope(result, started_at=t0, model=gen.name, citations=result.get("citations"))


@router.post("/analytics")
def ai_analytics(req: AnalyticsRequest, db: Session = Depends(get_db)):
    t0 = time.perf_counter()

    ds = db.get(Dataset, req.dataset)
    if ds is None:
        ds = (
            db.query(Dataset)
            .filter(or_(Dataset.title.ilike(f"%{req.dataset}%"), Dataset.id == req.dataset))
            .first()
        )
    if ds is None:
        raise HTTPException(404, f"Dataset '{req.dataset}' not found")

    variable = ds.variables[0] if ds.variables else "value"
    q = db.query(DatasetPoint).filter(DatasetPoint.dataset_id == ds.id)
    q = q.filter(DatasetPoint.variable == variable)

    if req.range and "-" in req.range:
        try:
            start, end = [p.strip() for p in req.range.split("-", 1)]
            q = q.filter(DatasetPoint.ts >= f"{start}-01-01", DatasetPoint.ts <= f"{end}-12-31")
        except Exception:
            pass

    if req.station and ds.station_id and req.station != ds.station_id:
        pass  # dataset already station-scoped; ignore mismatch

    pts = q.order_by(DatasetPoint.ts).all()
    if not pts:
        raise HTTPException(404, f"No observations for dataset '{req.dataset}'")

    values = np.asarray([p.value for p in pts], dtype="float64")
    series = [{"ts": p.ts, "value": p.value} for p in pts]

    op = (req.op or "mean").lower()
    if op == "mean":
        value = float(values.mean())
    elif op == "max":
        value = float(values.max())
    elif op == "min":
        value = float(values.min())
    elif op == "sum":
        value = float(values.sum())
    elif op in ("trend", "slope"):
        x = np.arange(len(values), dtype="float64")
        value = float(np.polyfit(x, values, 1)[0]) if len(values) > 1 else 0.0
    else:  # delta
        value = float(values[-1] - values[0])

    delta = float(values[-1] - values[0])

    data = {
        "dataset": {
            "id": ds.id,
            "title": ds.title,
            "station": ds.station_id,
            "theme": ds.theme,
            "year": ds.year,
            "unit": pts[0].unit,
            "license": ds.license,
            "authority": ds.authority,
            "updateFrequency": ds.update_frequency,
        },
        "variable": variable,
        "op": op,
        "range": [pts[0].ts, pts[-1].ts],
        "series": series,
        "value": round(value, 4),
        "delta": round(delta, 4),
        "observations": len(pts),
    }
    return envelope(
        data,
        started_at=t0,
        note="Prototype analytics computed over the seeded archive.",
    )
