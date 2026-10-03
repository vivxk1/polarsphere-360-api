"""Load the demo universe and run the full ingestion pipeline over it."""
from __future__ import annotations

import random
import sys
import time
import uuid

from sqlalchemy import text as sa_text

from .db import SessionLocal, engine, init_db
from .ingest import ingest_document
from .models import (
    Base,
    Chunk,
    Dataset,
    DatasetPoint,
    Document,
    Expedition,
    ExpeditionEvent,
    ExpeditionMember,
    KgEdge,
    KgNode,
    MapFeature,
    Media,
    Station,
)
from .seed_data import (
    DATASETS,
    DOCUMENTS,
    EXPEDITION,
    EXPEDITION_EVENTS,
    EXPEDITION_MEMBERS,
    MAP_LAYERS,
    MEDIA,
    STATIONS,
    THEME_LABELS,
)


def _series_for(dataset: dict) -> list[dict]:
    """Deterministic pseudo time series so analytics has something real to compute."""
    span = dataset.get("span", "annual")
    if span == "static":
        return []

    rng = random.Random(sum(ord(c) for c in dataset["title"]))

    if span == "decadal":
        times = [f"{y}-09-30" for y in range(2009, 2024)]
    else:
        times = [f"{dataset['year']}-{m:02d}-15" for m in range(1, 13)]

    out = []
    for var in dataset["variables"]:
        base = rng.uniform(-18.0, 4.0)
        drift = rng.uniform(-0.35, 0.35)
        noise = rng.uniform(0.15, 1.2)
        for i, ts in enumerate(times):
            value = base + drift * i + rng.gauss(0.0, noise)
            out.append({"variable": var, "ts": ts, "value": round(value, 3), "unit": dataset["unit"]})
    return out


def run(force: bool = False) -> None:
    started = time.perf_counter()

    if force:
        Base.metadata.drop_all(bind=engine)
    init_db()

    db = SessionLocal()
    try:
        if db.query(Document).count() > 0 and not force:
            print("Seed data already present. Use --force to rebuild.")
            return

        # ---- stations -----------------------------------------------------
        for s in STATIONS:
            db.merge(Station(**s))
        db.commit()
        print(f"stations: {len(STATIONS)}")

        # ---- expedition ---------------------------------------------------
        db.merge(Expedition(**EXPEDITION))
        db.commit()
        for e in EXPEDITION_EVENTS:
            db.add(ExpeditionEvent(id=str(uuid.uuid4()), expedition_id=EXPEDITION["id"], **e))
        for m in EXPEDITION_MEMBERS:
            db.add(ExpeditionMember(id=str(uuid.uuid4()), expedition_id=EXPEDITION["id"], **m))
        db.commit()
        print(f"expedition: {EXPEDITION['id']} ({len(EXPEDITION_EVENTS)} events, {len(EXPEDITION_MEMBERS)} members)")

        # ---- documents + ingestion ---------------------------------------
        total_chunks = 0
        for d in DOCUMENTS:
            doc = Document(
                id=str(uuid.uuid4()),
                title=d["title"],
                doc_type=d["doc_type"],
                station_id=d.get("station_id"),
                expedition_id=EXPEDITION["id"],
                theme=d["theme"],
                year=d["year"],
                abstract=d["abstract"],
                license="CC BY 4.0",
                authority="NCPOR",
                status="published",
            )
            db.add(doc)
            db.commit()
            n = ingest_document(db, doc, d["body"])
            total_chunks += n
            print(f"  ingested {n:>3} chunks  {d['title'][:52]}")
        print(f"documents: {len(DOCUMENTS)}  chunks: {total_chunks}")

        # ---- datasets -----------------------------------------------------
        for spec in DATASETS:
            ds = Dataset(
                id=str(uuid.uuid4()),
                title=spec["title"],
                station_id=spec.get("station_id"),
                expedition_id=EXPEDITION["id"],
                theme=spec["theme"],
                year=spec["year"],
                format=spec["format"],
                variables=spec["variables"],
                rows=spec["rows"],
                size_label=spec["size_label"],
                abstract=spec["abstract"],
            )
            db.add(ds)
            db.commit()
            pts = _series_for(spec)
            for p in pts:
                db.add(DatasetPoint(id=str(uuid.uuid4()), dataset_id=ds.id, **p))
            db.commit()
        print(f"datasets: {len(DATASETS)}")

        # ---- media --------------------------------------------------------
        for m in MEDIA:
            db.add(
                Media(
                    id=str(uuid.uuid4()),
                    title=m["title"],
                    media_type=m["media_type"],
                    station_id=m.get("station_id"),
                    expedition_id=EXPEDITION["id"],
                    theme=m["theme"],
                    year=m["year"],
                    thumb=f"/media/{m['media_type']}/{m['title'].lower().replace(' ', '-')}.jpg",
                    transcript=m["transcript"],
                    tags=m["tags"],
                )
            )
        db.commit()
        print(f"media: {len(MEDIA)}")

        # ---- map features -------------------------------------------------
        for f in MAP_LAYERS:
            db.add(MapFeature(id=str(uuid.uuid4()), **f))
        db.commit()
        print(f"map features: {len(MAP_LAYERS)}")

        # ---- knowledge graph ----------------------------------------------
        docs = db.query(Document).all()
        for doc in docs:
            db.merge(KgNode(id=doc.id, label=doc.title, kind=doc.doc_type))
        for theme, label in THEME_LABELS.items():
            db.merge(KgNode(id=f"theme:{theme}", label=label, kind="theme"))
        db.commit()

        by_theme: dict[str, list] = {}
        for doc in docs:
            by_theme.setdefault(doc.theme, []).append(doc.id)
            db.add(
                KgEdge(id=str(uuid.uuid4()), source=doc.id, target=f"theme:{doc.theme}", relation="has_theme")
            )
        for theme, ids in by_theme.items():
            for a, b in zip(ids, ids[1:]):
                db.add(KgEdge(id=str(uuid.uuid4()), source=a, target=b, relation="same_theme"))
        db.commit()
        node_count = db.query(KgNode).count()
        edge_count = db.query(KgEdge).count()
        print(f"knowledge graph: {node_count} nodes, {edge_count} edges")

        # ---- indexes ------------------------------------------------------
        db.execute(sa_text("CREATE INDEX IF NOT EXISTS idx_chunks_tsv ON chunks USING gin(tsv)"))
        db.execute(
            sa_text(
                "CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks "
                "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
            )
        )
        db.commit()

    finally:
        db.close()

    print(f"\nSeed complete in {time.perf_counter() - started:.1f}s")


if __name__ == "__main__":
    run(force="--force" in sys.argv)
