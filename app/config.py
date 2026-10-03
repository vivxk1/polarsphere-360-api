"""Central settings. Everything has a sane default so the stack boots with no .env."""
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://polarsphere:polarsphere@localhost:5433/polarsphere",
)

EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBED_DIM = int(os.getenv("EMBED_DIM", "384"))

LLM_BACKEND = os.getenv("LLM_BACKEND", "local")  # local | openai | extractive
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
LLM_PRELOAD = os.getenv("LLM_PRELOAD", "1")  # warm model weights at startup
LLM_MAX_NEW_TOKENS = int(os.getenv("LLM_MAX_NEW_TOKENS", "256"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
# CPU inference thread count. Benchmarked: 4 is ~6x faster than 16 for this model.
LLM_THREADS = int(os.getenv("LLM_THREADS", "4"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

CORS_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()
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
