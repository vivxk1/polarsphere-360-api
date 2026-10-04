# PolarSphere 360 — Backend

FastAPI backend for **SIH 2026 / PS 26063** — the integrated polar science
outreach, knowledge repository and media dissemination portal.

It replaces the deterministic mocks in the Next.js frontend with a real
retrieval and generation stack, while keeping the exact response shape documented
in `docs/backend-integration.md`: every endpoint returns `{ data, provenance }`.

---

## Requirements

| Requirement | Notes |
|---|---|
| **Python 3.9+** | Tested on 3.11. On Python 3.9 use `python3 -m uvicorn` — the `uvicorn` script may not land on `PATH`. |
| **Docker Desktop** | Required for Postgres 16 + pgvector. Without it nothing runs. |
| **~4 GB disk** | ~90 MB MiniLM embeddings + ~3 GB Qwen2.5-1.5B, downloaded on first run and cached. |

## Quick start

```bash
# 1. Postgres 16 + pgvector
docker compose up -d

# 2. Python deps
pip install -r requirements.txt

# 3. Seed the demo universe and run ingestion
python -m app.seed --force

# 4. Run the API
uvicorn app.main:app --reload --port 8000

# 5. Smoke test
python scripts/smoke_test.py
```

No API key is required. The RAG generator runs **locally** (Qwen2.5-1.5B-Instruct
via transformers, CPU only), so the stack works offline and costs nothing.

---

## What is actually real

| Capability | Status |
|---|---|
| Hybrid search (pgvector cosine + `tsvector`, fused with RRF) | ✅ real |
| Embeddings (`all-MiniLM-L6-v2`) | ✅ real, computed at ingest |
| RAG answers with source citations | ✅ real, grounded in retrieved passages |
| PDF / text ingestion → chunk → embed → index | ✅ real (PyMuPDF) |
| Dataset analytics (mean / min / max / trend / delta) | ✅ real, computed over stored series |
| Outreach drafting + 5-stage human approval | ✅ real generation, persisted workflow |
| Claim → source mapping | ✅ real (token-overlap attribution) |
| Knowledge graph relations | ✅ real adjacency table |

## Deliberate simplifications

These were in the original architecture but are not needed at this scale. Each can
be upgraded without changing the API surface.

- **PostGIS → jsonb.** `/api/map/features` only ever returns GeoJSON, so a spatial
  engine is unnecessary.
- **Neo4j → adjacency table.** The knowledge graph is small and static.
- **Redis → none.** No caching layer yet.
- **S3/MinIO → local filesystem.** Uploads land in `data/uploads/`.
- **Whisper → not wired.** Video transcripts are seeded as text.

## Configuration

Copy `.env.example` to `.env`. Notable keys:

| Key | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://...@localhost:5433/...` | Postgres with pgvector |
| `EMBED_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Semantic search + retrieval |
| `LLM_BACKEND` | `local` | `local` \| `openai` \| `extractive` |
| `LLM_MODEL` | `Qwen/Qwen2.5-1.5B-Instruct` | Local generator |
| `LLM_MAX_NEW_TOKENS` | `256` | Answer length cap |
| `CORS_ORIGINS` | `http://localhost:3000` | Next.js dev origin |

To swap in a hosted model later: set `LLM_BACKEND=openai` and `OPENAI_API_KEY=...`.
Nothing else changes — the generator is behind a single interface in `app/llm.py`.

---

## Endpoints

| Method | Path | Returns |
|---|---|---|
| GET | `/api/expeditions` | list |
| GET | `/api/expeditions/{id}` | detail + timeline + team |
| GET | `/api/stations` | list |
| GET | `/api/stations/{id}` | profile + counts + weather preview |
| POST | `/api/search` | documents + datasets + media |
| POST | `/api/ai/query` | answer + citations + related |
| POST | `/api/ai/analytics` | series + value + delta + source |
| POST | `/api/documents/upload` | jobId + ingest steps |
| GET | `/api/documents/{id}` | metadata + entities |
| POST | `/api/outreach/generate` | content + hashtags + claims |
| POST | `/api/outreach/{id}/approve` | stage + timestamps + history |
| GET | `/api/map/features?layer=` | GeoJSON FeatureCollection |
| POST | `/api/field/observation` | queued receipt |
| POST | `/api/field/sync` | sync count |
| POST | `/api/citizen/annotation` | consensus state |
| GET | `/api/admin/repository-health` | KPIs + pipeline + health |

Plus `/health` and `/api/contract` (self-describing route list).

---

## Grounding guarantee

The RAG generator only ever sees retrieved passages. It is instructed to cite
`[n]` on every factual sentence, and post-processing **strips citation markers
that point outside the retrieved set**. If retrieval returns nothing, the endpoint
answers *"The archive does not contain enough evidence to answer that."* rather
than inventing something.

If the generator fails to load, the endpoint degrades to **extractive mode** —
verbatim passages with citations — so it never silently hallucinates.

---

## Reconciling with the frontend

The contracts here were derived from `docs/backend-integration.md`, which lists
endpoints but not field-level TypeScript types. Before wiring the frontend, diff
`src/services/clients.ts` against `app/models.py` / `app/routers/*.py` and align
any field-name differences (for example `doc_type` vs `docType`).

`GET /api/contract` prints the live route table to speed that up.
