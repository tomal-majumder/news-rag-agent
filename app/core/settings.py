from pathlib import Path
import os

# Root of project (two levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Data dir: defaults to ./data locally, /home/data in Azure
DATA_DIR = Path(os.getenv("DATA_DIR", PROJECT_ROOT / "data")).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Chroma vector store location
SAMPLE_TYPE = 'tiny'  # or make env-configurable
CHROMA_DIR = DATA_DIR / "vector_store" / SAMPLE_TYPE
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# DB URL: defaults to SQLite file in DATA_DIR
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(DATA_DIR / 'news.db').as_posix()}")

# CORS origin
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")
