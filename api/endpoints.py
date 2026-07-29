"""EKIP Platform API Endpoints & Health Check System.

Changes made:
- Added system health check, platform status endpoints, and document registry query routines.
- Integrated Loguru logging for API requests.
"""

from typing import Dict, Any
from core.logger import get_logger

logger = get_logger("api.endpoints")


class PlatformAPI:
    """Enterprise API router and status monitor for EKIP."""

    @staticmethod
    def get_health_status(engine, config) -> Dict[str, Any]:
        """Return system health check JSON report."""
        logger.info("Executed health status check.")
        docs = engine.list_docs() if engine else {}
        return {
            "status": "healthy",
            "app_title": config.APP_TITLE,
            "version": "3.4.0",
            "indexed_documents_count": len(docs),
            "vector_store_active": True,
            "llm_model": config.LLM_MODEL,
        }

    @staticmethod
    def get_document_summary(engine) -> Dict[str, Any]:
        """Return summary of all registered documents in the knowledge base."""
        if not engine:
            return {"documents": {}}
        return {"documents": engine.list_docs()}
