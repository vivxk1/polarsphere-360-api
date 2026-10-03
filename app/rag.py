"""Retrieve-then-generate with mandatory citations.

Grounding rule: the generator only ever sees retrieved passages, and every
sentence it emits must carry a [n] marker. If the generator returns nothing
usable (or is running in extractive mode) we fall back to an assembled answer
built purely from the passages - never free-form invention.
"""
from __future__ import annotations

import re
from typing import Optional

from sqlalchemy.orm import Session

from .config import CONSENSUS_POOL, SERVICE_NAME
from .llm import get_generator
from .search import hybrid_search

SYSTEM_PROMPT = (
    "You are Polar AI, an assistant for India's polar research programme (NCPOR). "
    "Answer ONLY using the numbered passages provided. Every factual sentence must end "
    "with a citation marker like [1] or [2] matching the passage it came from. "
    "If the passages do not contain the answer, say exactly: "
    "\"The archive does not contain enough evidence to answer that.\" "
    "Be concise, factual, and never add information from outside the passages."
)


def _build_context(passages: list[dict]) -> str:
    parts = []
    for i, p in enumerate(passages, start=1):
        title = p.get("title") or "Untitled"
        station = p.get("station_id") or "unknown station"
        year = p.get("year") or "n.d."
        parts.append(f"[{i}] {title} ({station}, {year})\n{p['text']}")
    return "\n\n".join(parts)


def _to_citations(passages: list[dict]) -> list[dict]:
    out = []
    for i, p in enumerate(passages, start=1):
        snippet = p["text"].strip().replace("\n", " ")
        out.append(
            {
                "index": i,
                "id": p.get("document_id") or "",
                "title": p.get("title") or "",
                "docType": p.get("doc_type"),
                "station": p.get("station_id"),
                "year": p.get("year"),
                "snippet": snippet[:280] + ("..." if len(snippet) > 280 else ""),
                "score": round(float(p.get("score") or 0.0), 6),
                "authority": p.get("authority"),
                "license": p.get("license"),
            }
        )
    return out


def _extractive_answer(q: str, passages: list[dict]) -> str:
    """Assemble an answer from passages without any generation."""
    lines = [
        f"Based on {len(passages)} passage(s) retrieved from the archive, here is what the "
        f"records say about \"{q}\":"
    ]
    for i, p in enumerate(passages, start=1):
        snippet = p["text"].strip().replace("\n", " ")
        if len(snippet) > 240:
            snippet = snippet[:240] + "..."
        lines.append(f"- {snippet} [{i}]")
    lines.append("")
    lines.append("(Extractive mode: passages are returned verbatim, no text was generated.)")
    return "\n".join(lines)


def _strip_ungrounded(answer: str, n_passages: int) -> str:
    """Drop citation markers that point outside the retrieved set."""
    def repl(m):
        idx = int(m.group(1))
        return m.group(0) if 1 <= idx <= n_passages else ""

    return re.sub(r"\[(\d+)\]", repl, answer)


def answer_question(
    db: Session,
    q: str,
    mode: str = "grounded",
    station: Optional[str] = None,
    top_k: int = 6,
) -> dict:
    passages = hybrid_search(db, q, station=station, limit=top_k)
    citations = _to_citations(passages)

    if not passages:
        return {
            "answer": "The archive does not contain enough evidence to answer that.",
            "citations": [],
            "related": [],
            "mode": mode,
            "generator": "none",
            "passageCount": 0,
        }

    gen = get_generator()
    answer = ""
    used = gen.name

    if gen.name != "extractive":
        try:
            user_prompt = (
                f"Question: {q}\n\nPassages:\n{_build_context(passages)}\n\n"
                f"Answer with citation markers."
            )
            answer = gen.generate(SYSTEM_PROMPT, user_prompt) or ""
        except Exception as exc:  # generation must never break the endpoint
            answer = ""
            used = f"extractive (fallback: {type(exc).__name__})"

    if not answer.strip():
        used = used if "fallback" in used else "extractive"
        answer = _extractive_answer(q, passages)
    else:
        answer = _strip_ungrounded(answer, len(passages))

    return {
        "answer": answer,
        "citations": citations,
        "related": _related(db, passages),
        "mode": mode,
        "generator": used,
        "passageCount": len(passages),
    }


def _related(db: Session, passages: list[dict]) -> list[dict]:
    """Neighbours in the knowledge graph for the top cited documents."""
    from .models import KgEdge, KgNode

    doc_ids = []
    for p in passages[:3]:
        did = p.get("document_id")
        if did and did not in doc_ids:
            doc_ids.append(did)

    if not doc_ids:
        return []

    out = []
    seen = set()
    for did in doc_ids:
        node = db.get(KgNode, did)
        seed_id = node.id if node else None
        if not seed_id:
            continue
        edges = (
            db.query(KgEdge).filter((KgEdge.source == seed_id) | (KgEdge.target == seed_id)).limit(4).all()
        )
        for e in edges:
            other = e.target if e.source == seed_id else e.source
            if other in seen:
                continue
            seen.add(other)
            n = db.get(KgNode, other)
            out.append(
                {
                    "id": other,
                    "label": n.label if n else other,
                    "kind": n.kind if n else "concept",
                    "relation": e.relation,
                    "from": seed_id,
                }
            )
    return out[:8]
