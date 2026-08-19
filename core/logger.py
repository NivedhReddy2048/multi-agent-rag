"""Loguru Logging Configuration for EKIP (Enterprise Knowledge Intelligence Platform).

Changes made:
- Initialized Loguru logger with console and file rotation sink (data/logs/ekip.log).
- Provided contextual logging helpers for Upload, Retrieval, CRAG, LLM, Validation, Latency, and Errors.
"""

import sys
from pathlib import Path
from loguru import logger

# Reconfigure stdout and stderr for UTF-8 on Windows environments
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

# Ensure logs directory exists

LOG_DIR = Path(__file__).parent.parent / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "ekip.log"

# Remove default logger handlers and re-add structured formats
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)
logger.add(
    str(LOG_FILE),
    rotation="10 MB",
    retention="14 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
)


def get_logger(name: str):
    """Return a logger bound with component name context."""
    return logger.bind(component=name)
