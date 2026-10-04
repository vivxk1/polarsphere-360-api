"""AI-drafted outreach content and the human approval workflow."""
from __future__ import annotations
from typing import Optional

import re
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import CONSENSUS_THRESHOLD
from ..db import get_db
from ..llm import get_generator
from ..models import APPROVAL_STAGES, Chunk, Document, Post
from ..schemas import ApproveRequest, OutreachGenerateRequest, envelope

router = APIRouter(prefix="/api/outreach", tags=["outreach"])

FORMAT_GUIDANCE = {
    "Blog Post": "Write 3 short paragraphs with a plain-language lead.",
    "Instagram Carousel": "Write 5 slides, each a single punchy sentence under 20 words.",
    "Instagram Caption": "Write one caption under 120 words plus emoji where natural.",
    "Twitter Thread": "Write 4 numbered posts, each under 240 characters.",
    "Press Release": "Write a headline, a dateline and three paragraphs.",
    "LinkedIn Post": "Write a professional post of about 150 words.",
    "Video Script": "Write a 60 second narration script with scene notes.",
}

SYSTEM = (
    "You are a science communication writer for India's polar research programme. "
    "Rewrite the provided source material for the requested audience and format. "
    "Use only facts present in the source. Do not invent numbers. "
    "Keep the tone accurate and accessible."
)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 20]


def _map_claims(content: str, chunks: list[Chunk], limit: int = 4) -> list[dict]:
    """Attach each claim sentence to its best-matching source passage."""

    def tokens(s: str) -> set[str]:
        return {w for w in re.findall(r"[a-z0-9]{4,}", s.lower())}

    chunk_tokens = [(c, tokens(c.text)) for c in chunks]
    claims = []
    for sent in _sentences(content)[:limit]:
        st = tokens(sent)
        best, best_score = None, 0.0
        for c, ct in chunk_tokens:
            if not ct:
                continue
            score = len(st & ct) / max(1, len(st))
            if score > best_score:
                best, best_score = c, score
        if best is None:
            continue
        snippet = best.text.strip().replace("\n", " ")
        claims.append(
            {
                "claim": sent[:220],
                "sourceChunkId": best.id,
                "sourceDocumentId": best.document_id,
                "snippet": snippet[:200] + ("..." if len(snippet) > 200 else ""),
                "confidence": round(min(best_score, 0.99), 2),
            }
        )
    return claims


@router.post("/generate")
def generate(req: OutreachGenerateRequest, db: Session = Depends(get_db)):
    t0 = time.perf_counter()

    doc = None
    if req.sourceId:
        doc = db.get(Document, req.sourceId)
    if doc is None:
        doc = db.query(Document).filter(Document.status == "published").first()
    if doc is None:
        raise HTTPException(404, "No source document available to generate from")

    chunks = (
        db.query(Chunk)
        .filter(Chunk.document_id == doc.id)
        .order_by(Chunk.chunk_index)
        .limit(8)
        .all()
    )
    context = "\n\n".join(f"[{i}] {c.text}" for i, c in enumerate(chunks, start=1))

    guidance = FORMAT_GUIDANCE.get(req.format, FORMAT_GUIDANCE["Blog Post"])
    user_prompt = (
        f"Audience: {req.audience}\n"
        f"Language: {req.language}\n"
        f"Format: {req.format}\n"
        f"Guidance: {guidance}\n\n"
        f"Source document: {doc.title}\n\n"
        f"Source passages:\n{context}\n\n"
        "Write the content now."
    )

    gen = get_generator()
    content = ""
    if gen.name != "extractive":
        try:
            content = gen.generate(SYSTEM, user_prompt) or ""
        except Exception:
            content = ""

    if not content.strip():
        content = (
            f"{doc.title}\n\n{doc.abstract}\n\n"
            f"(Extractive draft - the generator is unavailable, so the source abstract is "
            f"returned verbatim for a human editor to rewrite.)"
        )

    hashtags = _hashtags(doc, req.audience)
    claims = _map_claims(content, chunks)

    post = Post(
        id=str(uuid.uuid4()),
        source_id=doc.id,
        audience=req.audience,
        language=req.language,
        format=req.format,
        content=content,
        hashtags=hashtags,
        claims=claims,
        stage="DRAFT",
        history=[{"stage": "DRAFT", "actor": "ai", "at": _now_iso()}],
    )
    db.add(post)
    db.commit()

    return envelope(
        {
            "id": post.id,
            "sourceId": doc.id,
            "sourceTitle": doc.title,
            "audience": req.audience,
            "language": req.language,
            "format": req.format,
            "content": content,
            "hashtags": hashtags,
            "claims": claims,
            "stage": post.stage,
            "createdAt": post.created_at.isoformat(),
        },
        started_at=t0,
        model=gen.name,
        citations=[
            {
                "index": 1,
                "id": doc.id,
                "title": doc.title,
                "snippet": (doc.abstract or "")[:200],
                "authority": doc.authority,
                "license": doc.license,
            }
        ],
        note="AI-assisted draft. Requires human approval before publishing.",
    )


def _hashtags(doc: Document, audience: str) -> list[str]:
    base = ["#PolarScience", "#NCPOR", "#IndiaInAntarctica"]
    if doc.station_id:
        base.append(f"#{doc.station_id.capitalize()}")
    if doc.theme:
        base.append("#" + "".join(w.capitalize() for w in doc.theme.split("-")))
    if "student" in audience.lower() or "school" in audience.lower():
        base.append("#STEMeducation")
    return base[:8]


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


@router.post("/{post_id}/approve")
def approve(post_id: str, req: ApproveRequest, db: Session = Depends(get_db)):
    t0 = time.perf_counter()
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(404, f"Post {post_id} not found")

    target = req.stage.upper().replace(" ", "_")
    if target not in APPROVAL_STAGES:
        idx = APPROVAL_STAGES.index(post.stage) if post.stage in APPROVAL_STAGES else 0
        target = APPROVAL_STAGES[min(idx + 1, len(APPROVAL_STAGES) - 1)]

    post.stage = target
    entry = {"stage": target, "actor": req.reviewer, "at": _now_iso()}
    post.history = list(post.history or []) + [entry]
    db.commit()

    return envelope(
        {
            "id": post.id,
            "stage": post.stage,
            "status": "approved" if post.stage in ("APPROVED", "PUBLISHED") else "in_review",
            "reviewer": req.reviewer,
            "updatedAt": post.updated_at.isoformat() if post.updated_at else None,
            "history": post.history,
            "nextStage": (
                APPROVAL_STAGES[APPROVAL_STAGES.index(target) + 1]
                if target != APPROVAL_STAGES[-1]
                else None
            ),
        },
        started_at=t0,
        note="Human approval recorded." if post.stage != "DRAFT" else None,
    )


@router.get("")
def list_posts(stage: Optional[str] = None, db: Session = Depends(get_db)):
    t0 = time.perf_counter()
    q = db.query(Post)
    if stage:
        q = q.filter(Post.stage == stage.upper())
    posts = q.order_by(Post.created_at.desc()).limit(50).all()
    data = [
        {
            "id": p.id,
            "sourceId": p.source_id,
            "audience": p.audience,
            "language": p.language,
            "format": p.format,
            "stage": p.stage,
            "hashtags": p.hashtags,
            "claimCount": len(p.claims or []),
            "createdAt": p.created_at.isoformat() if p.created_at else None,
        }
        for p in posts
    ]
    return envelope(data, started_at=t0)
