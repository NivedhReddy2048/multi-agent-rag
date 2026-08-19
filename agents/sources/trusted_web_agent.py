"""Trusted Web Knowledge Agent using TrustedWebProviderManager (Tavily primary with DuckDuckGo fallback)."""

import time
from typing import List
from agents.sources.base_agent import BaseKnowledgeAgent
from core.models.domain import KnowledgeResult, SourceType
from core.providers.trusted_web import trusted_web_provider_manager
from core.logger import get_logger

logger = get_logger("agents.sources.trusted_web_agent")


class TrustedWebKnowledgeAgent(BaseKnowledgeAgent):
    """Retrieves live web knowledge snippets via TrustedWebProviderManager."""

    def __init__(self):
        super().__init__(
            agent_name="TrustedWebKnowledgeAgent",
            source_type=SourceType.TRUSTED_WEB,
            provider_key="trusted_web"
        )
        self.manager = trusted_web_provider_manager

    def initialize(self) -> bool:
        self.is_initialized = True
        return True

    def health(self) -> bool:
        return self.manager.health()

    def execute(self, query: str, max_results: int = 5) -> List[KnowledgeResult]:
        t0 = time.time()
        results: List[KnowledgeResult] = []

        res = self.manager.search(query, max_results=max_results)
        lat = (time.time() - t0) * 1000

        if res and res.success and res.data:
            raw_items = res.data if isinstance(res.data, list) else res.data.get("results", [])
            provider_used = res.provider or "trusted_web"
            for item in raw_items:
                title = item.get("title", "Web Result")
                content = item.get("content", item.get("snippet", item.get("body", "")))
                url = item.get("url", item.get("link", item.get("href", "")))
                score = item.get("score", 0.8 if provider_used == "tavily" else 0.7)
                results.append(KnowledgeResult(
                    provider=provider_used,
                    source_type=SourceType.TRUSTED_WEB,
                    title=title,
                    content=content,
                    url=url,
                    confidence=float(score),
                    latency_ms=lat,
                    metadata={"url": url, "provider_used": provider_used},
                ))
            if results:
                logger.info(f"TrustedWebKnowledgeAgent retrieved {len(results)} items via {provider_used} in {int(lat)}ms")
                return results

        return results

