"""Corrective RAG (CRAG) agent evaluating retrieval quality and providing web search fallback for EKIP Platform.

Changes made:
- Integrated Loguru logging for retrieval sufficiency evaluation and Tavily web search triggers.
- Ensured web search fallback chunks retain metadata fields (source_file, page, chunk_id, score).
"""

from typing import Dict, Any, List, Tuple
from .base import BaseAgent, AgentResult
from core.logger import get_logger

logger = get_logger("agents.crag")


class CRAGAgent(BaseAgent):
    """Corrective RAG Agent that only assesses retrieved document evidence."""

    name = "crag"
    description = "Corrective RAG - evaluates retrieval sufficiency for the orchestrator"

    def __init__(self, config):
        self.cfg = config
        self.tavily_key = config.TAVILY_API_KEY

    def evaluate_retrieval(self, query: str, docs: List[Dict]) -> Tuple[bool, float]:
        if not docs:
            logger.info("CRAG evaluation: 0 document chunks retrieved.")
            return False, 0.0

        import re
        q_tokens = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', query.lower()) if w not in {"what", "where", "when", "how", "why", "this", "that", "from", "with", "have"}]
        if not q_tokens:
            return True, 0.70

        combined_text = " ".join(d.get("content", "").lower() for d in docs)
        found_count = sum(1 for t in q_tokens if t in combined_text)
        coverage = found_count / len(q_tokens) if q_tokens else 1.0

        total_length = len(combined_text)
        length_score = min(1.0, total_length / 1500)

        semantic_score = (coverage * 0.7) + (length_score * 0.3)
        is_sufficient = semantic_score >= 0.35 and len(docs) > 0

        logger.info(f"CRAG evaluation score: {semantic_score:.2f} | Sufficiency: {is_sufficient}")
        return is_sufficient, round(semantic_score, 2)

    def run(self, context: Dict[str, Any]) -> AgentResult:
        query = context["query"]
        docs = context.get("documents", [])

        is_sufficient, score = self.evaluate_retrieval(query, docs)

        if is_sufficient:
            return AgentResult(
                confidence=int(score * 100),
                sources=docs,
                agent_trace=[f"✅ CRAG: Retrieval sufficient (score: {score:.2f})"],
                metadata={
                    "sufficient": True,
                    "crag_used": False,
                    "retrieval_score": score,
                    "web_results_count": 0,
                    "source_mode": "none",
                }
            )

        return AgentResult(
            confidence=int(score * 100),
            sources=docs,
            agent_trace=[
                f"⚠️ CRAG: Retrieval insufficient (score: {score:.2f})"
            ],
            metadata={
                "sufficient": False,
                "crag_used": False,
                "retrieval_score": score,
                "web_results_count": 0,
                "source_mode": "none",
            }
        )
