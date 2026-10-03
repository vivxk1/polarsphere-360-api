"""Expeditions, stations and map layers."""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import (
    Dataset,
    DatasetPoint,
    Document,
    Expedition,
    ExpeditionEvent,
    ExpeditionMember,
    MapFeature,
    Media,
    Station,
)
from ..schemas import envelope

router = APIRouter(prefix="/api", tags=["core"])


@router.get("/expeditions")
def list_expeditions(db: Session = Depends(get_db)):
    t0 = time.perf_counter()
    rows = db.query(Expedition).all()
    data = [
        {
            "id": e.id,
            "name": e.name,
            "season": e.season,
            "status": e.status,
            "startDate": e.start_date,
            "endDate": e.end_date,
            "summary": e.summary,
            "leadInstitution": e.lead_institution,
            "memberCount": db.query(ExpeditionMember).filter(ExpeditionMember.expedition_id == e.id).count(),
            "documentCount": db.query(Document).filter(Document.expedition_id == e.id).count(),
        }
        for e in rows
    ]
    return envelope(data, started_at=t0)


@router.get("/expeditions/{expedition_id}")
def get_expedition(expedition_id: str, db: Session = Depends(get_db)):
    t0 = time.perf_counter()
    e = db.get(Expedition, expedition_id)
    if not e:
        raise HTTPException(404, f"Expedition {expedition_id} not found")

    events = (
        db.query(ExpeditionEvent)
        .filter(ExpeditionEvent.expedition_id == e.id)
        .order_by(ExpeditionEvent.date)
        .all()
    )
    members = db.query(ExpeditionMember).filter(ExpeditionMember.expedition_id == e.id).all()

    data = {
        "id": e.id,
        "name": e.name,
        "season": e.season,
        "status": e.status,
        "startDate": e.start_date,
        "endDate": e.end_date,
        "summary": e.summary,
        "leadInstitution": e.lead_institution,
        "timeline": [
            {"date": ev.date, "title": ev.title, "description": ev.description, "kind": ev.kind}
            for ev in events
        ],
        "team": [
            {"name": m.name, "role": m.role, "organisation": m.organisation, "isLead": m.is_lead}
            for m in members
        ],
        "documents": db.query(Document).filter(Document.expedition_id == e.id).count(),
        "datasets": db.query(Dataset).filter(Dataset.expedition_id == e.id).count(),
        "media": db.query(Media).filter(Media.expedition_id == e.id).count(),
    }
    return envelope(data, started_at=t0)


@router.get("/stations/{station_id}")
def get_station(station_id: str, db: Session = Depends(get_db)):
    t0 = time.perf_counter()
    s = db.get(Station, station_id)
    if not s:
        raise HTTPException(404, f"Station {station_id} not found")

    latest = (
        db.query(DatasetPoint)
        .join(Dataset, Dataset.id == DatasetPoint.dataset_id)
        .filter(Dataset.station_id == s.id)
        .order_by(DatasetPoint.ts.desc())
        .first()
    )

    data = {
        "id": s.id,
        "name": s.name,
        "region": s.region,
        "stationType": s.station_type,
        "established": s.established,
        "lat": s.lat,
        "lon": s.lon,
        "summary": s.summary,
        "meta": s.meta,
        "counts": {
            "documents": db.query(Document).filter(Document.station_id == s.id).count(),
            "datasets": db.query(Dataset).filter(Dataset.station_id == s.id).count(),
            "media": db.query(Media).filter(Media.station_id == s.id).count(),
        },
        "weatherPreview": (
            {
                "variable": latest.variable,
                "value": latest.value,
                "unit": latest.unit,
                "observedAt": latest.ts,
            }
            if latest
            else None
        ),
    }
    return envelope(data, started_at=t0)


@router.get("/stations")
def list_stations(db: Session = Depends(get_db)):
    t0 = time.perf_counter()
    rows = db.query(Station).all()
    data = [
        {
            "id": s.id,
            "name": s.name,
            "region": s.region,
            "lat": s.lat,
            "lon": s.lon,
            "established": s.established,
            "summary": s.summary,
        }
        for s in rows
    ]
    return envelope(data, started_at=t0)


@router.get("/map/features")
def map_features(layer: str | None = None, db: Session = Depends(get_db)):
    t0 = time.perf_counter()
    q = db.query(MapFeature)
    if layer:
        q = q.filter(MapFeature.layer == layer)
    rows = q.all()

    data = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": r.properties, "geometry": r.geometry} for r in rows
        ],
        "layers": sorted({r.layer for r in rows}),
    }
    return envelope(data, started_at=t0)
