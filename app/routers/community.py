"""Citizen science annotations and FieldSync offline observations."""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import CONSENSUS_POOL, CONSENSUS_THRESHOLD
from ..db import get_db
from ..models import Annotation, Observation
from ..schemas import CitizenAnnotationRequest, FieldObservationRequest, envelope

router = APIRouter(prefix="/api", tags=["community"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/field/observation")
def queue_observation(req: FieldObservationRequest, db: Session = Depends(get_db)):
    t0 = time.perf_counter()
    obs = Observation(
        id=str(uuid.uuid4()),
        station_id=req.stationId,
        payload=req.payload,
        status="queued",
        queued_at=_now(),
    )
    db.add(obs)
    db.commit()

    return envelope(
        {
            "receiptId": obs.id,
            "status": obs.status,
            "stationId": obs.station_id,
            "queuedAt": obs.queued_at.isoformat(),
            "note": "Stored offline-first. Will sync when connectivity returns.",
        },
        started_at=t0,
    )


@router.post("/field/sync")
def sync_observations(db: Session = Depends(get_db)):
    t0 = time.perf_counter()
    pending = db.query(Observation).filter(Observation.status == "queued").all()
    for obs in pending:
        obs.status = "synced"
        obs.synced_at = _now()
    db.commit()

    return envelope(
        {"synced": len(pending), "status": "ok", "syncedAt": _now().isoformat()},
        started_at=t0,
    )


@router.post("/citizen/annotation")
def annotate(req: CitizenAnnotationRequest, db: Session = Depends(get_db)):
    t0 = time.perf_counter()

    ann = (
        db.query(Annotation)
        .filter(Annotation.media_id == req.mediaId, Annotation.label == req.label)
        .first()
    )
    if ann is None:
        ann = Annotation(
            id=str(uuid.uuid4()),
            media_id=req.mediaId,
            label=req.label,
            votes=[],
            consensus=False,
            created_at=_now(),
        )
        db.add(ann)

    votes = list(ann.votes or [])
    if req.voter not in votes:
        votes.append(req.voter)
    ann.votes = votes
    ann.consensus = len(set(votes)) >= CONSENSUS_THRESHOLD
    db.commit()

    return envelope(
        {
            "id": ann.id,
            "mediaId": ann.media_id,
            "label": ann.label,
            "votes": ann.votes,
            "voteCount": len(ann.votes),
            "consensus": ann.consensus,
            "threshold": CONSENSUS_THRESHOLD,
            "pool": CONSENSUS_POOL,
            "state": "consensus_reached" if ann.consensus else "awaiting_review",
        },
        started_at=t0,
        note=f"{len(ann.votes)}/{CONSENSUS_POOL} votes; {CONSENSUS_THRESHOLD} needed for consensus.",
    )


@router.get("/citizen/annotations")
def list_annotations(mediaId: str | None = None, db: Session = Depends(get_db)):
    t0 = time.perf_counter()
    q = db.query(Annotation)
    if mediaId:
        q = q.filter(Annotation.media_id == mediaId)
    rows = q.order_by(Annotation.created_at.desc()).limit(100).all()
    data = [
        {
            "id": a.id,
            "mediaId": a.media_id,
            "label": a.label,
            "votes": a.votes,
            "consensus": a.consensus,
            "createdAt": a.created_at.isoformat() if a.created_at else None,
        }
        for a in rows
    ]
    return envelope(data, started_at=t0)
