"""Repository health for the admin dashboard."""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import EMBED_MODEL, LLM_BACKEND, LLM_MODEL
from ..db import get_db
from ..llm import get_generator
from ..models import (
    Annotation,
    Chunk,
    Dataset,
    Document,
    Expedition,
    IngestJob,
    KgEdge,
    KgNode,
    Media,
    Observation,
    Post,
    Station,
)
from ..schemas import envelope

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/repository-health")
def repository_health(db: Session = Depends(get_db)):
    t0 = time.perf_counter()

    doc_count = db.query(Document).count()
    chunk_count = db.query(Chunk).count()
    indexed = db.query(Chunk).filter(Chunk.embedding.isnot(None)).count()
    pending_review = db.query(Document).filter(Document.status != "published").count()

    pipeline = {
        "uploaded": doc_count,
        "indexed": indexed,
        "pendingReview": pending_review,
        "failed": db.query(IngestJob).filter(IngestJob.status == "failed").count(),
        "untagged": db.query(Document).filter(Document.theme == "unclassified").count(),
    }

    kpis = {
        "documents": doc_count,
        "chunks": chunk_count,
        "datasets": db.query(Dataset).count(),
        "media": db.query(Media).count(),
        "stations": db.query(Station).count(),
        "expeditions": db.query(Expedition).count(),
        "knowledgeNodes": db.query(KgNode).count(),
        "knowledgeEdges": db.query(KgEdge).count(),
        "observationsQueued": db.query(Observation).filter(Observation.status == "queued").count(),
        "annotations": db.query(Annotation).count(),
        "postsInReview": db.query(Post).filter(Post.stage.in_(["DRAFT", "SCIENTIST_REVIEW", "COMMUNICATION_REVIEW"])).count(),
        "indexCoverage": round(indexed / chunk_count, 4) if chunk_count else 0.0,
    }

    gen = get_generator()
    health = {
        "database": "ok",
        "vectorIndex": "ok" if indexed else "empty",
        "embeddingModel": EMBED_MODEL,
        "generator": gen.name,
        "generatorBackend": LLM_BACKEND,
        "generatorModel": LLM_MODEL,
        "status": "degraded" if pending_review or not indexed else "ok",
    }

    suggestions = []
    if pending_review:
        suggestions.append(f"{pending_review} document(s) are awaiting human review before publishing.")
    if chunk_count and indexed < chunk_count:
        suggestions.append(f"{chunk_count - indexed} chunk(s) have no embedding; re-run ingestion.")
    if not doc_count:
        suggestions.append("Archive is empty. Run the seed script or upload documents.")
    if db.query(Document).filter(Document.theme == "unclassified").count():
        suggestions.append("Some uploads are untagged; assign a theme to improve retrieval.")
    if not suggestions:
        suggestions.append("Repository is healthy. Consider adding more expedition seasons.")

    return envelope(
        {"kpis": kpis, "pipeline": pipeline, "health": health, "suggestions": suggestions},
        started_at=t0,
    )
