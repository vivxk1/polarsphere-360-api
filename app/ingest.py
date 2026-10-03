"""Document ingestion: extract -> chunk -> embed -> index."""
from __future__ import annotations

import uuid

from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session

from .config import CHUNK_OVERLAP, CHUNK_SIZE
from .embed import embed_texts
from .models import Chunk


def extract_pdf_text(path: str) -> str:
    import fitz  # PyMuPDF

    with fitz.open(path) as doc:
        return "\n\n".join(page.get_text("text") for page in doc)


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Word-window chunking with overlap. Simple, predictable, good enough for reports."""
    words = text.split()
    if not words:
        return []
    step = max(1, size - overlap)
    chunks = []
    start = 0
    while start < len(words):
        piece = words[start : start + size]
        if not piece:
            break
        chunks.append(" ".join(piece))
        start += step
    return chunks


def ingest_document(db: Session, document, body: str, batch_size: int = 32) -> int:
    """Chunk + embed + store. Returns the number of chunks created."""
    chunks = chunk_text(body)
    if not chunks:
        return 0

    created = 0
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        vecs = embed_texts(batch)
        for offset, (c, v) in enumerate(zip(batch, vecs)):
            db.add(
                Chunk(
                    id=str(uuid.uuid4()),
                    document_id=document.id,
                    chunk_index=start + offset,
                    text=c,
                    embedding=v.tolist(),
                )
            )
            created += 1
    db.commit()

    # Populate the lexical index for full-text search.
    db.execute(
        sa_text("UPDATE chunks SET tsv = to_tsvector('english', text) WHERE document_id = :d"),
        {"d": document.id},
    )
    db.commit()
    return created


INGEST_STEPS = [
    "upload_received",
    "format_detected",
    "text_extracted",
    "metadata_tagged",
    "chunked",
    "embedded",
    "indexed",
    "awaiting_review",
]
