"""Hierarchical report generation agent for EKIP Platform.

Changes made:
- Added Loguru logging for report synthesis steps.
- Implemented multi-model fallback list for LLM report generation.
"""

from typing import Dict, Any
from .base import BaseAgent, AgentResult
from core.logger import get_logger
from core.llm_manager import LLMManager

logger = get_logger("agents.report")


class ReportAgent(BaseAgent):
    """Compatibility adapter for report synthesis; routing remains in OrchestratorAgent."""

    name = "report"
    description = "Report-format synthesis adapter without retrieval, fallbacks, or routing"

    def __init__(self, config, engine, synthesis_agent):
        self.cfg = config
        self.engine = engine  # retained for backwards-compatible construction
        self.synthesis = synthesis_agent

    def run(self, context: Dict[str, Any]) -> AgentResult:
        query = context["query"]
        documents = context.get("documents", [])
        source_mode = context.get("source_mode", "documents" if documents else "none")
        logger.info("ReportAgent received {} orchestrator-selected evidence sources.", len(documents))
        result = self.synthesis.run({
            "query": query,
            "documents": documents,
            "history": context.get("history", []),
            "intent": "REPORT",
            "source_mode": source_mode,
        })
        result.agent_trace.insert(0, "📊 Report format synthesis")
        return result
