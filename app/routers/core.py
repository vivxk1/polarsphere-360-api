"""Expeditions, stations and map layers."""
from __future__ import annotations
from typing import Optional

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
def map_features(layer: Optional[str] = None, db: Session = Depends(get_db)):
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


@router.get("/datasets")
def list_datasets(station: Optional[str] = None, theme: Optional[str] = None, db: Session = Depends(get_db)):
    """Catalogue of tabular/netCDF datasets. Used by the Data page."""
    t0 = time.perf_counter()
    q = db.query(Dataset)
    if station:
        q = q.filter(Dataset.station_id == station)
    if theme:
        q = q.filter(Dataset.theme == theme)
    rows = q.all()

    data = [
        {
            "id": d.id,
            "title": d.title,
            "station": d.station_id,
            "theme": d.theme,
            "year": d.year,
            "format": d.format,
            "variables": d.variables or [],
            "rows": d.rows,
            "sizeLabel": d.size_label,
            "abstract": d.abstract,
            "license": d.license,
            "authority": d.authority,
        }
        for d in rows
    ]
    return envelope(data, started_at=t0)


@router.get("/media")
def list_media(station: Optional[str] = None, kind: Optional[str] = None, db: Session = Depends(get_db)):
    """Media catalogue — images, video and audio with transcripts."""
    t0 = time.perf_counter()
    q = db.query(Media)
    if station:
        q = q.filter(Media.station_id == station)
    if kind:
        q = q.filter(Media.media_type == kind)
    rows = q.all()

    data = [
        {
            "id": m.id,
            "title": m.title,
            "kind": m.media_type,
            "station": m.station_id,
            "theme": m.theme,
            "year": m.year,
            "thumb": m.thumb,
            "license": m.license,
            "tags": m.tags or [],
            "hasTranscript": bool(m.transcript),
        }
        for m in rows
    ]
    return envelope(data, started_at=t0)
