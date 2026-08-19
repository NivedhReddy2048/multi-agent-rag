"""Corrective RAG (CRAG) agent evaluating retrieval quality and providing web search fallback for EKIP Platform.

Changes made:
- Integrated Loguru logging for retrieval sufficiency evaluation and Tavily web search triggers.
- Ensured web search fallback chunks retain metadata fields (source_file, page, chunk_id, score).
"""

from typing import Dict, Any, List, Tuple, Optional
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

    def evaluate_retrieval(self, query: str, docs: List[Dict], source_strategy: Optional[Any] = None) -> Tuple[bool, float]:
        if not docs:
            logger.info("CRAG evaluation: 0 document chunks retrieved.")
            return False, 0.0

        from core.planner.enums import SourceStrategy
        if isinstance(source_strategy, SourceStrategy):
            is_strict = (source_strategy == SourceStrategy.DOCUMENT_ONLY)
        elif source_strategy:
            is_strict = (str(source_strategy).lower() == "document_only")
        else:
            is_strict = False

        min_score = float(getattr(self.cfg, "MIN_RERANK_SCORE_STRICT", -1.0)) if is_strict else float(getattr(self.cfg, "MIN_RERANK_SCORE", 0.0))
        surviving = [d for d in docs if "score" not in d or float(d.get("score", 0.0)) >= min_score]

        if not surviving:
            logger.info("CRAG evaluation: 0 document chunks survived relevance threshold.")
            return False, 0.0

        import re
        import math

        q_tokens = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', query.lower()) if w not in {"what", "where", "when", "how", "why", "this", "that", "from", "with", "have"}]
        if not q_tokens:
            return True, 0.70

        combined_text = " ".join(d.get("content", "").lower() for d in surviving)
        found_count = sum(1 for t in q_tokens if t in combined_text)
        coverage = found_count / len(q_tokens) if q_tokens else 1.0

        # CrossEncoder rerank score fallback signal for low-keyword-overlap scenarios
        scores = [float(d.get("score")) for d in surviving if d.get("score") is not None]
        max_rerank_score = max(scores) if scores else None

        if max_rerank_score is not None and max_rerank_score >= min_score:
            # Chunk passed strategy-aware CrossEncoder threshold: base relevance signal is at least 0.50
            rerank_signal = 0.50
        else:
            rerank_signal = 0.0

        # If token coverage is low, allow relevant CrossEncoder signal to preserve sufficient status
        effective_relevance = max(coverage, rerank_signal)

        total_length = len(combined_text)
        length_score = min(1.0, total_length / 1500)

        semantic_score = (effective_relevance * 0.7) + (length_score * 0.3)
        is_sufficient = semantic_score >= 0.35 and len(surviving) > 0

        logger.info(f"CRAG evaluation score: {semantic_score:.2f} (cov: {coverage:.2f}, rerank_sig: {rerank_signal:.2f}) | Sufficiency: {is_sufficient} ({len(surviving)}/{len(docs)} chunks)")
        return is_sufficient, round(semantic_score, 2)

    def run(self, context: Dict[str, Any]) -> AgentResult:
        query = context["query"]
        docs = context.get("documents", [])
        source_strategy = context.get("source_strategy")
        if not source_strategy and context.get("execution_plan"):
            source_strategy = getattr(context["execution_plan"], "source_strategy", None)

        from core.planner.enums import SourceStrategy
        if isinstance(source_strategy, SourceStrategy):
            is_strict = (source_strategy == SourceStrategy.DOCUMENT_ONLY)
        elif source_strategy:
            is_strict = (str(source_strategy).lower() == "document_only")
        else:
            is_strict = False

        min_score = float(getattr(self.cfg, "MIN_RERANK_SCORE_STRICT", -1.0)) if is_strict else float(getattr(self.cfg, "MIN_RERANK_SCORE", 0.0))
        surviving_docs = [d for d in docs if "score" not in d or float(d.get("score", 0.0)) >= min_score]

        is_sufficient, score = self.evaluate_retrieval(query, surviving_docs, source_strategy=source_strategy)

        if is_sufficient:
            return AgentResult(
                confidence=int(score * 100),
                sources=surviving_docs,
                agent_trace=[f"✅ CRAG: Retrieval sufficient (score: {score:.2f})"],
                metadata={
                    "sufficient": True,
                    "crag_used": False,
                    "retrieval_score": score,
                    "web_results_count": 0,
                    "source_mode": "none",
                    "chunks_entering_crag_count": len(docs),
                    "chunks_surviving_crag_count": len(surviving_docs),
                }
            )

        return AgentResult(
            confidence=int(score * 100),
            sources=surviving_docs,
            agent_trace=[
                f"⚠️ CRAG: Retrieval insufficient (score: {score:.2f})"
            ],
            metadata={
                "sufficient": False,
                "crag_used": False,
                "retrieval_score": score,
                "web_results_count": 0,
                "source_mode": "none",
                "chunks_entering_crag_count": len(docs),
                "chunks_surviving_crag_count": len(surviving_docs),
            }
        )

