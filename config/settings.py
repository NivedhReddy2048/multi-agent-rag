"""EKIP Enterprise Configuration Module.

Changes made:
- Added comprehensive settings for Gemini models (gemini-2.0-flash with fallback list).
- Defined paths for ChromaDB, Observability DB, upload directory, and log files.
- Added environment variable validation and safety defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Enterprise Configuration for EKIP Platform."""

    APP_TITLE: str = "Enterprise Knowledge Intelligence Platform (EKIP)"
    APP_TAGLINE: str = "AI-powered Multi-Agent Enterprise Knowledge Management Platform"
    APP_ICON: str = "🧠"

    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    COHERE_API_KEY: str = os.getenv("COHERE_API_KEY", "")
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

    # Provider Order Strategy
    PROVIDER_PRIORITY: list = ["gemini", "groq", "cohere", "mistral"]

    # Supported LLM Providers & Models Config
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    GEMINI_FALLBACK_MODEL: str = "gemini-1.5-flash"

    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_FALLBACK_MODEL: str = "llama-3.1-8b-instant"

    COHERE_MODEL: str = os.getenv("COHERE_MODEL", "command-r-plus")
    COHERE_FALLBACK_MODEL: str = "command-r"

    MISTRAL_MODEL: str = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
    MISTRAL_FALLBACK_MODEL: str = "mistral-small-latest"

    GEMINI_MODELS: list = ["gemini-2.0-flash", "gemini-1.5-flash"]
    GROQ_MODELS: list = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    COHERE_MODELS: list = ["command-r-plus", "command-r"]
    MISTRAL_MODELS: list = ["mistral-large-latest", "mistral-small-latest"]

    LLM_MODEL: str = GEMINI_MODEL
    LLM_FALLBACK_MODELS: list = ["gemini-2.0-flash", "gemini-1.5-flash", "llama-3.3-70b-versatile", "command-r-plus", "mistral-large-latest"]

    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    CHROMA_PATH: str = os.getenv("CHROMA_DB_PATH", str(DATA_DIR / "chroma_db"))
    OBSERVABILITY_DB: str = os.getenv("DB_PATH", str(DATA_DIR / "observability.db"))
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    LOG_DIR: Path = DATA_DIR / "logs"

    # Retrieval & Web Search Tuning
    ENABLE_WEB_SEARCH: bool = os.getenv("ENABLE_WEB_SEARCH", "true").lower() in ("true", "1", "yes")
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_DENSE: int = 8
    TOP_K_SPARSE: int = 8
    RERANK_TOP_K: int = 6
    CONFIDENCE_THRESHOLD: float = 0.25

    # LLM Performance & Reliability Tuning
    LLM_TIMEOUT_SECONDS: float = 10.0
    LLM_MAX_RETRIES: int = 1  # Transient network error retry budget
    LLM_MAX_FALLBACK_MODELS: int = 2
    LLM_MAX_WAIT_SECONDS: float = 2.0

    # Cache
    CACHE_TTL_MINUTES: int = 30

    @classmethod
    def ensure_dirs(cls):
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        Path(cls.CHROMA_PATH).mkdir(parents=True, exist_ok=True)
        Path(cls.OBSERVABILITY_DB).parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def print_startup_diagnostics(cls):
        """Print audit diagnostics during system initialization."""
        print("=" * 60)
        print("  EKIP MULTI-LLM SUBSYSTEM STARTUP AUDIT DIAGNOSTICS")
        print("=" * 60)
        print(f"  Gemini API Key Loaded  : {'YES (' + str(len(cls.GEMINI_API_KEY)) + ' chars)' if cls.GEMINI_API_KEY else 'NO (MISSING)'}")
        print(f"  Groq API Key Loaded    : {'YES (' + str(len(cls.GROQ_API_KEY)) + ' chars)' if cls.GROQ_API_KEY else 'NO (MISSING)'}")
        print(f"  Cohere API Key Loaded  : {'YES (' + str(len(cls.COHERE_API_KEY)) + ' chars)' if cls.COHERE_API_KEY else 'NO (MISSING)'}")
        print(f"  Mistral API Key Loaded : {'YES (' + str(len(cls.MISTRAL_API_KEY)) + ' chars)' if cls.MISTRAL_API_KEY else 'NO (MISSING)'}")
        print(f"  Provider Priority Order: {cls.PROVIDER_PRIORITY}")
        print(f"  Embedding Model        : {cls.EMBEDDING_MODEL}")
        print(f"  ChromaDB Storage Path  : {cls.CHROMA_PATH}")
        print(f"  Observability DB Path  : {cls.OBSERVABILITY_DB}")
        print(f"  LLM Timeout Budget     : {cls.LLM_TIMEOUT_SECONDS} seconds")
        print("=" * 60)

    @classmethod
    def validate(cls):
        cls.ensure_dirs()
        cls.print_startup_diagnostics()


Config.ensure_dirs()
