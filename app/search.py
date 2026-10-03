"""Hybrid retrieval: pgvector cosine search fused with Postgres full-text via RRF."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import text as sqltext
from sqlalchemy.orm import Session

from .embed import embed_one

RRF_K = 60  # Reciprocal Rank Fusion damping constant


def _filters(station: Optional[str], theme: Optional[str], year: Optional[int], source: Optional[str]) -> tuple[str, dict]:
    clauses = []
    params: dict = {}
    if station:
        clauses.append("AND d.station_id = :station")
        params["station"] = station
    if theme:
        clauses.append("AND d.theme = :theme")
        params["theme"] = theme
    if year:
        clauses.append("AND d.year = :year")
        params["year"] = int(year)
    if source:
        clauses.append("AND d.authority = :source")
        params["source"] = source
    return " ".join(clauses), params


def _vec_literal(vec: list[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"


def vector_search(db: Session, q: str, k: int = 20, **filters) -> list[dict]:
    clause, params = _filters(
        filters.get("station"), filters.get("theme"), filters.get("year"), filters.get("source")
    )
    params["vec"] = _vec_literal(embed_one(q))
    params["k"] = k
    rows = db.execute(
        sqltext(
            f"""
            SELECT c.id, c.document_id, c.text, c.page,
                   1 - (c.embedding <=> CAST(:vec AS vector)) AS score,
                   d.title, d.doc_type, d.station_id, d.year, d.authority, d.license
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.embedding IS NOT NULL {clause}
            ORDER BY c.embedding <=> CAST(:vec AS vector)
            LIMIT :k
            """
        ),
        params,
    ).mappings().all()
    return [dict(r) for r in rows]


def fulltext_search(db: Session, q: str, k: int = 20, **filters) -> list[dict]:
    clause, params = _filters(
        filters.get("station"), filters.get("theme"), filters.get("year"), filters.get("source")
    )
    params["q"] = q
    params["k"] = k
    rows = db.execute(
        sqltext(
            f"""
            SELECT c.id, c.document_id, c.text, c.page,
                   ts_rank(to_tsvector('english', c.text), plainto_tsquery(:q)) AS score,
                   d.title, d.doc_type, d.station_id, d.year, d.authority, d.license
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE to_tsvector('english', c.text) @@ plainto_tsquery(:q) {clause}
            ORDER BY score DESC
            LIMIT :k
            """
        ),
        params,
    ).mappings().all()
    return [dict(r) for r in rows]


def hybrid_search(
    db: Session,
    q: str,
    station: Optional[str] = None,
    theme: Optional[str] = None,
    year: Optional[int] = None,
    source: Optional[str] = None,
    limit: int = 10,
    k: int = 20,
) -> list[dict]:
    """Fuse vector and lexical results with Reciprocal Rank Fusion."""
    if not q.strip():
        return []

    vec_hits = vector_search(db, q, k=k, station=station, theme=theme, year=year, source=source)
    ft_hits = fulltext_search(db, q, k=k, station=station, theme=theme, year=year, source=source)

    fused: dict[str, dict] = {}
    for rank, hit in enumerate(vec_hits):
        row = dict(hit)
        row["rrf"] = 1.0 / (RRF_K + rank + 1)
        row["vec_score"] = float(hit.get("score") or 0.0)
        row["ft_score"] = 0.0
        fused[row["id"]] = row
    for rank, hit in enumerate(ft_hits):
        key = hit["id"]
        if key in fused:
            fused[key]["rrf"] += 1.0 / (RRF_K + rank + 1)
            fused[key]["ft_score"] = float(hit.get("score") or 0.0)
        else:
            row = dict(hit)
            row["rrf"] = 1.0 / (RRF_K + rank + 1)
            row["vec_score"] = 0.0
            row["ft_score"] = float(hit.get("score") or 0.0)
            fused[key] = row

    results = sorted(fused.values(), key=lambda r: r["rrf"], reverse=True)[:limit]
    for r in results:
        r["score"] = round(float(r["rrf"]), 6)
    return results
