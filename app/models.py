"""ORM models.

Design note: PostGIS and Neo4j from the original architecture are deliberately
not used. GeoJSON is stored as jsonb (the map endpoint only ever returns GeoJSON
features) and the knowledge graph is a plain adjacency pair. Both can be upgraded
later without touching the API surface.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .config import EMBED_DIM
from .db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.utcnow()


class Station(Base):
    __tablename__ = "stations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # maitri | bharati | himadri
    name: Mapped[str] = mapped_column(String(128))
    region: Mapped[str] = mapped_column(String(64), default="Antarctica")
    station_type: Mapped[str] = mapped_column(String(64), default="research station")
    established: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    summary: Mapped[str] = mapped_column(Text, default="")
    hero_image: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)


class Expedition(Base):
    __tablename__ = "expeditions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # 43rd-isea
    name: Mapped[str] = mapped_column(String(160))
    season: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(32), default="completed")
    start_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    lead_institution: Mapped[str] = mapped_column(String(128), default="NCPOR")
    meta: Mapped[dict] = mapped_column(JSON, default=dict)

    timeline: Mapped[list["ExpeditionEvent"]] = relationship(back_populates="expedition", cascade="all, delete-orphan")
    members: Mapped[list["ExpeditionMember"]] = relationship(back_populates="expedition", cascade="all, delete-orphan")


class ExpeditionEvent(Base):
    __tablename__ = "expedition_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    expedition_id: Mapped[str] = mapped_column(ForeignKey("expeditions.id"))
    date: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    kind: Mapped[str] = mapped_column(String(32), default="milestone")

    expedition: Mapped[Expedition] = relationship(back_populates="timeline")


class ExpeditionMember(Base):
    __tablename__ = "expedition_members"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    expedition_id: Mapped[str] = mapped_column(ForeignKey("expeditions.id"))
    name: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(128))
    organisation: Mapped[str] = mapped_column(String(128), default="")
    is_lead: Mapped[bool] = mapped_column(default=False)

    expedition: Mapped[Expedition] = relationship(back_populates="members")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(300))
    doc_type: Mapped[str] = mapped_column(String(64), default="report")
    station_id: Mapped[str | None] = mapped_column(ForeignKey("stations.id"), nullable=True)
    expedition_id: Mapped[str | None] = mapped_column(ForeignKey("expeditions.id"), nullable=True)
    theme: Mapped[str] = mapped_column(String(64), default="")
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    abstract: Mapped[str] = mapped_column(Text, default="")
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    license: Mapped[str] = mapped_column(String(128), default="CC BY 4.0")
    authority: Mapped[str] = mapped_column(String(128), default="NCPOR")
    update_frequency: Mapped[str] = mapped_column(String(64), default="per expedition")
    status: Mapped[str] = mapped_column(String(32), default="published")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"))
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    text: Mapped[str] = mapped_column(Text)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding = mapped_column(Vector(EMBED_DIM), nullable=True)
    tsv = mapped_column(TSVECTOR, nullable=True)

    document: Mapped[Document] = relationship(back_populates="chunks")


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(300))
    station_id: Mapped[str | None] = mapped_column(ForeignKey("stations.id"), nullable=True)
    expedition_id: Mapped[str | None] = mapped_column(ForeignKey("expeditions.id"), nullable=True)
    theme: Mapped[str] = mapped_column(String(64), default="")
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    format: Mapped[str] = mapped_column(String(32), default="CSV")
    variables: Mapped[list] = mapped_column(JSON, default=list)
    rows: Mapped[int] = mapped_column(Integer, default=0)
    size_label: Mapped[str] = mapped_column(String(64), default="")
    license: Mapped[str] = mapped_column(String(128), default="CC BY 4.0")
    authority: Mapped[str] = mapped_column(String(128), default="NCPOR")
    update_frequency: Mapped[str] = mapped_column(String(64), default="daily")
    abstract: Mapped[str] = mapped_column(Text, default="")

    points: Mapped[list["DatasetPoint"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")


class DatasetPoint(Base):
    """Time series used by POST /api/ai/analytics."""

    __tablename__ = "dataset_points"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id"))
    variable: Mapped[str] = mapped_column(String(64))
    ts: Mapped[str] = mapped_column(String(32))  # ISO date
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(32), default="")

    dataset: Mapped[Dataset] = relationship(back_populates="points")


class Media(Base):
    __tablename__ = "media"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(300))
    media_type: Mapped[str] = mapped_column(String(32), default="image")  # image | video | audio
    station_id: Mapped[str | None] = mapped_column(ForeignKey("stations.id"), nullable=True)
    expedition_id: Mapped[str | None] = mapped_column(ForeignKey("expeditions.id"), nullable=True)
    theme: Mapped[str] = mapped_column(String(64), default="")
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    thumb: Mapped[str] = mapped_column(String(512), default="")
    license: Mapped[str] = mapped_column(String(128), default="CC BY 4.0")
    transcript: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)


class Post(Base):
    """AI-drafted outreach content moving through human approval."""

    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    audience: Mapped[str] = mapped_column(String(64), default="General Public")
    language: Mapped[str] = mapped_column(String(8), default="en")
    format: Mapped[str] = mapped_column(String(64), default="Blog Post")
    content: Mapped[str] = mapped_column(Text, default="")
    hashtags: Mapped[list] = mapped_column(JSON, default=list)
    claims: Mapped[list] = mapped_column(JSON, default=list)
    stage: Mapped[str] = mapped_column(String(32), default="DRAFT")
    history: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class Annotation(Base):
    """Citizen science labels with N-of-M consensus."""

    __tablename__ = "annotations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    media_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    label: Mapped[str] = mapped_column(String(128))
    votes: Mapped[list] = mapped_column(JSON, default=list)
    consensus: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Observation(Base):
    """FieldSync: queued offline, synced later."""

    __tablename__ = "observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    station_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    queued_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class MapFeature(Base):
    """GeoJSON feature per layer."""

    __tablename__ = "map_features"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    layer: Mapped[str] = mapped_column(String(64), index=True)
    properties: Mapped[dict] = mapped_column(JSON, default=dict)
    geometry: Mapped[dict] = mapped_column(JSON, default=dict)


class KgNode(Base):
    __tablename__ = "kg_nodes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(64), default="concept")
    weight: Mapped[float] = mapped_column(Float, default=1.0)


class KgEdge(Base):
    __tablename__ = "kg_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source: Mapped[str] = mapped_column(ForeignKey("kg_nodes.id"))
    target: Mapped[str] = mapped_column(ForeignKey("kg_nodes.id"))
    relation: Mapped[str] = mapped_column(String(64), default="related_to")


class IngestJob(Base):
    __tablename__ = "ingest_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    filename: Mapped[str] = mapped_column(String(300))
    document_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    steps: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


# Approval stages used by the outreach workflow
APPROVAL_STAGES = ["DRAFT", "SCIENTIST_REVIEW", "COMMUNICATION_REVIEW", "APPROVED", "PUBLISHED"]
