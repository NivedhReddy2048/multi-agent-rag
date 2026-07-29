"""Document management and CRUD agent for EKIP Platform.

Changes made:
- Added Loguru logging for document deletion and listing operations.
"""

from typing import Dict, Any
from .base import BaseAgent, AgentResult
from core.logger import get_logger

logger = get_logger("agents.admin")


class AdminAgent(BaseAgent):
    """Admin Agent managing document CRUD tasks and system state operations."""

    name = "admin"
    description = "Handles document CRUD and system status"

    def __init__(self, engine):
        self.engine = engine

    def run(self, context: Dict[str, Any]) -> AgentResult:
        action = context.get("action", "delete")
        doc_name = context.get("doc_name", "")

        if action == "delete" or "delete" in str(context.get("query", "")).lower():
            logger.info(f"AdminAgent deleting document '{doc_name}'")
            result = self.engine.delete_document(doc_name)
            if result.startswith("DELETED"):
                return AgentResult(
                    content=f"✅ Successfully deleted document `{doc_name}`.",
                    confidence=100,
                    agent_trace=[f"🗑️ Deleted {doc_name} from ChromaDB and BM25 index"],
                    metadata={"source_mode": "none"},
                )
            logger.warning(f"AdminAgent delete failed for document '{doc_name}'")
            return AgentResult(
                content=f"⚠️ Could not delete `{doc_name}`. Document not found.",
                confidence=100,
                success=False,
                agent_trace=[f"⚠️ Delete failed: {doc_name} not found"],
                metadata={"source_mode": "none"},
            )

        if action == "list":
            docs = self.engine.list_docs()
            logger.info(f"AdminAgent listed {len(docs)} documents")
            return AgentResult(
                content=str(docs),
                confidence=100,
                metadata={"docs": docs, "source_mode": "none"}
            )

        return AgentResult(content="Unknown admin action", success=False, metadata={"source_mode": "none"})
