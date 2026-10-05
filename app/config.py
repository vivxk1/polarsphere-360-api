"""Central settings. Everything has a sane default so the stack boots with no .env."""
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://polarsphere:polarsphere@localhost:5433/polarsphere",
)

EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBED_DIM = int(os.getenv("EMBED_DIM", "384"))
# local  - sentence-transformers in-process. Default; no API key, works offline.
# openai - hosted embeddings, needs OPENAI_API_KEY. Use this where torch cannot
#          be installed (e.g. Vercel's 250 MB serverless function limit).
EMBED_BACKEND = os.getenv("EMBED_BACKEND", "local")  # local | openai
EMBED_OPENAI_MODEL = os.getenv("EMBED_OPENAI_MODEL", "text-embedding-3-small")

LLM_BACKEND = os.getenv("LLM_BACKEND", "local")  # local | openai | extractive
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
LLM_PRELOAD = os.getenv("LLM_PRELOAD", "1")  # warm model weights at startup
LLM_MAX_NEW_TOKENS = int(os.getenv("LLM_MAX_NEW_TOKENS", "256"))
# 0.0 = greedy decoding. A 1.5B model at temperature 0.2 gave noticeably
# unstable answers (including spurious abstentions) between identical requests,
# which is bad in a demo. Greedy is deterministic and correctly grounded.
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))
# CPU inference thread count. Benchmarked: 4 is ~6x faster than 16 for this model.
LLM_THREADS = int(os.getenv("LLM_THREADS", "4"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001",
    ).split(",")
    if o.strip()
]

# Chunking
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))

# Citizen science consensus rule: N of M matching votes
CONSENSUS_THRESHOLD = int(os.getenv("CONSENSUS_THRESHOLD", "2"))
CONSENSUS_POOL = int(os.getenv("CONSENSUS_POOL", "3"))

UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "uploads"))
SEED_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "seed")

SERVICE_NAME = "polarsphere360-api"
SERVICE_VERSION = "0.1.0"
