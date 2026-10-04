"""Hybrid search plus document upload and metadata."""
from __future__ import annotations

import os
import time
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import UPLOAD_DIR
from ..db import get_db
from ..ingest import INGEST_STEPS, extract_pdf_text, ingest_document
from ..models import Dataset, Document, IngestJob, Media
from ..schemas import SearchRequest, envelope
from ..search import hybrid_search

router = APIRouter(prefix="/api", tags=["search"])


def _doc_card(p: dict) -> dict:
    return {
        "id": p.get("document_id"),
        "title": p.get("title"),
        "docType": p.get("doc_type"),
        "station": p.get("station_id"),
        "year": p.get("year"),
        "snippet": p["text"][:240] + ("..." if len(p["text"]) > 240 else ""),
        "score": p.get("score"),
        "authority": p.get("authority"),
        "license": p.get("license"),
        "matchedBy": (
            "hybrid"
            if (p.get("vec_score") and p.get("ft_score"))
            else ("semantic" if p.get("vec_score") else "lexical")
        ),
    }


@router.post("/search")
def search(req: SearchRequest, db: Session = Depends(get_db)):
    t0 = time.perf_counter()
    kind = (req.type or "all").lower()

    documents = []
    if kind in ("all", "documents", "docs"):
        if req.q.strip():
            # over-fetch when narrowing by docType, then trim back to the limit
            fetch = min(req.limit * 4, 200) if req.docType else req.limit
            hits = hybrid_search(
                db, req.q, station=req.station, theme=req.theme, year=req.year,
                source=req.source, limit=fetch,
            )
            documents = [_doc_card(p) for p in hits]
            if req.docType:
                documents = [
                    d for d in documents if (d.get("docType") or "").lower() == req.docType.lower()
                ][: req.limit]
        else:
            q = db.query(Document)
            if req.station:
                q = q.filter(Document.station_id == req.station)
            if req.theme:
                q = q.filter(Document.theme == req.theme)
            if req.year:
                q = q.filter(Document.year == req.year)
            if req.docType:
                q = q.filter(Document.doc_type == req.docType)
            documents = [
                {
                    "id": d.id,
                    "title": d.title,
                    "docType": d.doc_type,
                    "station": d.station_id,
                    "year": d.year,
                    "snippet": d.abstract,
                    "score": None,
                    "authority": d.authority,
                    "license": d.license,
                    "matchedBy": "browse",
                }
                for d in q.limit(req.limit).all()
            ]

    datasets = []
    if kind in ("all", "datasets", "data"):
        q = db.query(Dataset)
        if req.station:
            q = q.filter(Dataset.station_id == req.station)
        if req.theme:
            q = q.filter(Dataset.theme == req.theme)
        if req.year:
            q = q.filter(Dataset.year == req.year)
        for d in q.limit(req.limit).all():
            if req.q.strip() and req.q.lower() not in (d.title + " " + d.abstract).lower():
                continue
            datasets.append(
                {
                    "id": d.id,
                    "title": d.title,
                    "station": d.station_id,
                    "theme": d.theme,
                    "year": d.year,
                    "format": d.format,
                    "variables": d.variables,
                    "rows": d.rows,
                    "size": d.size_label,
                    "license": d.license,
                    "authority": d.authority,
                    "updateFrequency": d.update_frequency,
                    "abstract": d.abstract,
                }
            )

    media = []
    if kind in ("all", "media"):
        q = db.query(Media)
        if req.station:
            q = q.filter(Media.station_id == req.station)
        if req.theme:
            q = q.filter(Media.theme == req.theme)
        for m in q.limit(req.limit).all():
            if req.q.strip() and req.q.lower() not in (m.title + " " + m.transcript).lower():
                continue
            media.append(
                {
                    "id": m.id,
                    "title": m.title,
                    "mediaType": m.media_type,
                    "station": m.station_id,
                    "theme": m.theme,
                    "year": m.year,
                    "thumb": m.thumb,
                    "license": m.license,
                    "transcript": m.transcript,
                    "tags": m.tags,
                }
            )

    data = {
        "query": req.q,
        "documents": documents,
        "datasets": datasets,
        "media": media,
        "total": len(documents) + len(datasets) + len(media),
    }
    return envelope(data, started_at=t0, note="hybrid: pgvector cosine + tsvector, fused with RRF")


@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    t0 = time.perf_counter()
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    job = IngestJob(id=str(uuid.uuid4()), filename=file.filename or "upload.bin", status="running")
    db.add(job)
    db.commit()

    dest = os.path.join(UPLOAD_DIR, f"{job.id}_{job.filename}")
    content = await file.read()
    with open(dest, "wb") as fh:
        fh.write(content)

    if dest.lower().endswith(".pdf"):
        body = extract_pdf_text(dest)
    else:
        body = content.decode("utf-8", errors="ignore")

    doc = Document(
        id=str(uuid.uuid4()),
        title=job.filename.rsplit(".", 1)[0],
        doc_type="upload",
        theme="unclassified",
        abstract=(body[:280] + "...") if len(body) > 280 else body,
        file_path=dest,
        status="awaiting_review",
    )
    db.add(doc)
    db.commit()

    chunks = ingest_document(db, doc, body)

    job.document_id = doc.id
    job.status = "awaiting_review"
    job.steps = [{"step": s, "status": "done"} for s in INGEST_STEPS[:-1]] + [
        {"step": INGEST_STEPS[-1], "status": "pending"}
    ]
    db.commit()

    return envelope(
        {
            "jobId": job.id,
            "documentId": doc.id,
            "filename": job.filename,
            "chunks": chunks,
            "status": job.status,
            "steps": job.steps,
        },
        started_at=t0,
    )


@router.get("/documents/{document_id}")
def get_document(document_id: str, db: Session = Depends(get_db)):
    t0 = time.perf_counter()
    d = db.get(Document, document_id)
    if not d:
        raise HTTPException(404, f"Document {document_id} not found")

    chunks = [c.text for c in d.chunks]
    blob = " ".join(chunks)[:6000]

    data = {
        "id": d.id,
        "title": d.title,
        "docType": d.doc_type,
        "station": d.station_id,
        "expedition": d.expedition_id,
        "theme": d.theme,
        "year": d.year,
        "abstract": d.abstract,
        "license": d.license,
        "authority": d.authority,
        "updateFrequency": d.update_frequency,
        "status": d.status,
        "pageCount": d.page_count,
        "chunkCount": len(chunks),
        "entities": _entities(blob),
        "createdAt": d.created_at.isoformat() if d.created_at else None,
    }
    return envelope(data, started_at=t0)


_KNOWN_TERMS = {
    "Maitri": "station",
    "Bharati": "station",
    "Himadri": "station",
    "Ny-Alesund": "place",
    "Prydz Bay": "place",
    "Schirmacher": "place",
    "Larsemann Hills": "place",
    "sea ice": "concept",
    "ice shelf": "concept",
    "permafrost": "concept",
    "black carbon": "concept",
    "aerosol": "concept",
    "Circumpolar Deep Water": "concept",
    "katabatic": "concept",
    "mass balance": "concept",
    "geomagnetic": "concept",
    "benthic": "concept",
    "metagenom": "concept",
    "Antarctic Bottom Water": "concept",
}


def _entities(text: str) -> list[dict]:
    """Naive gazetteer extraction. Replace with a real NER model later."""
    low = text.lower()
    out = []
    for term, kind in _KNOWN_TERMS.items():
        count = low.count(term.lower())
        if count:
            out.append(
                {
                    "name": term,
                    "kind": kind,
                    "confidence": round(min(0.55 + 0.12 * count, 0.97), 2),
                    "mentions": count,
                }
            )
    return sorted(out, key=lambda e: e["mentions"], reverse=True)[:12]
