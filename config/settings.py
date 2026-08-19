"""EKIP Enterprise Configuration Module.

Changes made:
- Added comprehensive settings for Gemini models (gemini-2.0-flash with fallback list).
- Defined paths for ChromaDB, Observability DB, upload directory, and log files.
- Added environment variable validation and safety defaults.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure UTF-8 output encoding for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

load_dotenv()



class Config:
    """Educational Configuration for EKIP Platform."""

    APP_TITLE: str = "Educational Knowledge Intelligence Platform (EKIP)"
    APP_TAGLINE: str = "Learn from Multiple Trusted Knowledge Sources — Your AI Learning Companion"
    APP_ICON: str = "🧠"


    # API Keys & Knowledge Provider Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    COHERE_API_KEY: str = os.getenv("COHERE_API_KEY", "")
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

    # Phase 2 Knowledge Providers
    JINA_API_KEY: str = os.getenv("JINA_API_KEY", "")
    FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY", "")
    SERPAPI_API_KEY: str = os.getenv("SERPAPI_API_KEY", "")
    DUCKDUCKGO_ENABLED: bool = os.getenv("DUCKDUCKGO_ENABLED", "true").lower() in ("true", "1", "yes")
    DUCKDUCKGO_REGION: str = os.getenv("DUCKDUCKGO_REGION", "us-en")
    DUCKDUCKGO_MAX_RESULTS: int = int(os.getenv("DUCKDUCKGO_MAX_RESULTS", "5"))
    DUCKDUCKGO_TIMEOUT: int = int(os.getenv("DUCKDUCKGO_TIMEOUT", "10"))
    TAVILY_MAX_RESULTS: int = int(os.getenv("TAVILY_MAX_RESULTS", "5"))
    TAVILY_TIMEOUT: int = int(os.getenv("TAVILY_TIMEOUT", "10"))
    SEMANTIC_SCHOLAR_API_KEY: str = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
    YOUTUBE_DATA_API_KEY: str = os.getenv("YOUTUBE_DATA_API_KEY", "")
    GOOGLE_BOOKS_API_KEY: str = os.getenv("GOOGLE_BOOKS_API_KEY", "")

    # Provider Order Strategy

    PROVIDER_PRIORITY: list = ["groq", "gemini", "mistral", "cohere"]

    # Supported LLM Providers & Models Config
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_FALLBACK_MODEL: str = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-2.5-flash")

    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    GROQ_FALLBACK_MODEL: str = os.getenv("GROQ_FALLBACK_MODEL", "openai/gpt-oss-20b")

    COHERE_MODEL: str = os.getenv("COHERE_MODEL", "command-r-08-2024")
    COHERE_FALLBACK_MODEL: str = os.getenv("COHERE_FALLBACK_MODEL", "command-r-08-2024")

    MISTRAL_MODEL: str = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
    MISTRAL_FALLBACK_MODEL: str = os.getenv("MISTRAL_FALLBACK_MODEL", "mistral-small-latest")

    GEMINI_MODELS: list = ["gemini-2.5-flash", "gemini-3.5-flash"]
    GROQ_MODELS: list = ["openai/gpt-oss-20b", "groq/compound"]
    COHERE_MODELS: list = ["command-r-08-2024"]
    MISTRAL_MODELS: list = ["mistral-large-latest", "mistral-small-latest"]

    LLM_MODEL: str = GEMINI_MODEL
    LLM_FALLBACK_MODELS: list = ["gemini-2.5-flash", "openai/gpt-oss-20b", "command-r-08-2024", "mistral-large-latest"]

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
    MIN_RERANK_SCORE: float = float(os.getenv("MIN_RERANK_SCORE", "-15.0"))
    MIN_RERANK_SCORE_STRICT: float = float(os.getenv("MIN_RERANK_SCORE_STRICT", "-15.0"))
    MAX_EVIDENCE_CHUNKS: int = int(os.getenv("MAX_EVIDENCE_CHUNKS", "4"))
    MAX_EVIDENCE_CHARS: int = int(os.getenv("MAX_EVIDENCE_CHARS", "3000"))


    # LLM Performance & Reliability Tuning
    LLM_TIMEOUT_SECONDS: float = 15.0
    LLM_MAX_RETRIES: int = 1  # Transient network error retry budget
    LLM_MAX_FALLBACK_MODELS: int = 2
    LLM_MAX_WAIT_SECONDS: float = 15.0

    # Cache
    CACHE_TTL_MINUTES: int = 30
    CACHE_BACKEND: str = os.getenv("CACHE_BACKEND", "memory")  # 'memory' or 'redis'
    CACHE_MAX_ENTRIES: int = 2000

    # Production & Environment Control
    ENV_MODE: str = os.getenv("ENV_MODE", "development").lower()  # 'development', 'staging', 'production'
    MAX_CONCURRENT_PROVIDER_TASKS: int = int(os.getenv("MAX_CONCURRENT_PROVIDER_TASKS", "50"))
    CIRCUIT_BREAKER_THRESHOLD: int = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "3"))
    CIRCUIT_BREAKER_RECOVERY_SEC: float = float(os.getenv("CIRCUIT_BREAKER_RECOVERY_SEC", "30.0"))
    MAX_INPUT_CHARACTERS: int = int(os.getenv("MAX_INPUT_CHARACTERS", "10000"))
    PROMPT_INJECTION_PROTECTION_ENABLED: bool = True

    # Feature Flags
    FEATURE_BACKGROUND_JOBS: bool = True
    FEATURE_EVENT_BUS: bool = True
    FEATURE_SECURITY_HARDENING: bool = True
    FEATURE_STREAMING_RESPONSES: bool = True

    @classmethod
    def get_provider_key(cls, provider_name: str):
        """Get API key for provider by string identifier."""
        name = provider_name.lower()
        key_map = {
            "gemini": cls.GEMINI_API_KEY,
            "groq": cls.GROQ_API_KEY,
            "cohere": cls.COHERE_API_KEY,
            "mistral": cls.MISTRAL_API_KEY,
            "tavily": cls.TAVILY_API_KEY,
            "github": cls.GITHUB_TOKEN,
            "jina": cls.JINA_API_KEY,
            "firecrawl": cls.FIRECRAWL_API_KEY,
            "serpapi": cls.SERPAPI_API_KEY,
            "duckduckgo": None,
            "semantic_scholar": cls.SEMANTIC_SCHOLAR_API_KEY,
            "wikipedia": None,
            "arxiv": None,
            "youtube": cls.YOUTUBE_DATA_API_KEY,
            "google_books": cls.GOOGLE_BOOKS_API_KEY,
        }
        return key_map.get(name)

    @classmethod
    def is_provider_configured(cls, provider_name: str) -> bool:
        """Check if provider credentials/settings are present."""
        name = provider_name.lower()
        if name in ("wikipedia", "arxiv"):
            return True
        if name == "duckduckgo":
            return bool(getattr(cls, "DUCKDUCKGO_ENABLED", True))
        key = cls.get_provider_key(name)
        return bool(key and key.strip())

    @classmethod
    def get_masked_key(cls, provider_name: str) -> str:
        """Return safe masked representation of API key without exposing secret."""
        name = provider_name.lower()
        if name in ("wikipedia", "arxiv"):
            return "PUBLIC_API (No Key Required)"
        if name == "duckduckgo":
            return "ENABLED" if getattr(cls, "DUCKDUCKGO_ENABLED", True) else "DISABLED"
        key = cls.get_provider_key(name)
        if not key or not key.strip():
            return "NOT_CONFIGURED"
        k = key.strip()
        if len(k) <= 8:
            return f"Configured ({k[:2]}***{k[-2:]})"
        return f"Configured ({k[:4]}...{k[-4:]})"

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
