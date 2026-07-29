"""Telemetry and Observability Module for EKIP Platform.

Changes made:
- Added TelemetryTracker to monitor query confidence, faithfulness, latency, CRAG triggers, agents used, tokens, and response time.
- Integrated Loguru structured logging for analytics events.
"""

from typing import List, Dict, Any, Optional
from core.logger import get_logger

logger = get_logger("analytics.telemetry")


class TelemetryTracker:
    """Enterprise Telemetry Metrics Collector."""

    @staticmethod
    def calculate_estimated_tokens(text: str) -> int:
        """Estimate token count based on character and word heuristics."""
        if not text:
            return 0
        words = text.split()
        return max(1, int(len(words) * 1.3))

    @classmethod
    def record_query_metrics(
        cls,
        memory_instance,
        query: str,
        intent: str,
        confidence: int,
        faithfulness: float,
        blocked: bool,
        latency_ms: int,
        agent_trace: List[str],
        source_mode: str = "none",
        crag_used: bool = False,
        web_results_count: int = 0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> Dict[str, Any]:
        """Record query telemetry metrics into SQLite database and Loguru logs."""
        total_tokens = prompt_tokens + completion_tokens
        if total_tokens == 0:
            total_tokens = cls.calculate_estimated_tokens(query) + cls.calculate_estimated_tokens(intent)

        metric_data = {
            "query": query,
            "intent": intent,
            "confidence": confidence,
            "faithfulness": faithfulness,
            "blocked": blocked,
            "latency_ms": latency_ms,
            "crag_used": crag_used,
            "web_results_count": web_results_count,
            "agents_used": agent_trace,
            "source_mode": source_mode,
            "tokens": total_tokens,
            "response_time_sec": round(latency_ms / 1000.0, 3),
        }

        # Log via Loguru
        logger.info(
            f"Query Telemetry | Intent: {intent} | Latency: {latency_ms}ms | "
            f"Confidence: {confidence}% | Faithfulness: {faithfulness} | "
            f"CRAG: {crag_used} | Source Mode: {source_mode} | Tokens: {total_tokens}"
        )

        # Record to memory storage
        if memory_instance:
            try:
                memory_instance.log_query_analytics(
                    query=query,
                    intent=intent,
                    confidence=confidence,
                    faithfulness=faithfulness,
                    blocked=blocked,
                    latency_ms=latency_ms,
                    agent_trace=agent_trace,
                    source_mode=source_mode,
                    crag_used=crag_used,
                    web_results_count=web_results_count,
                    tokens=total_tokens,
                )
            except Exception as e:
                logger.error(f"Failed to record query telemetry to database: {e}")

        return metric_data
