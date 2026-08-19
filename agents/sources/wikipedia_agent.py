"""Wikipedia Knowledge Agent wrapping Wikipedia Provider."""

import time
from typing import List
from agents.sources.base_agent import BaseKnowledgeAgent
from core.models.domain import KnowledgeResult, SourceType
from core.providers import provider_registry
from core.logger import get_logger

logger = get_logger("agents.sources.wikipedia_agent")


class WikipediaKnowledgeAgent(BaseKnowledgeAgent):
    """Retrieves Wikipedia encyclopedic background summaries."""

    def __init__(self):
        super().__init__(
            agent_name="WikipediaKnowledgeAgent",
            source_type=SourceType.WIKIPEDIA,
            provider_key="wikipedia"
        )

    def initialize(self) -> bool:
        self.is_initialized = True
        return True

    def health(self) -> bool:
        p = provider_registry.get_provider("wikipedia")
        return p is not None

    def execute(self, query: str, max_results: int = 3) -> List[KnowledgeResult]:
        t0 = time.time()
        results: List[KnowledgeResult] = []

        wiki_p = provider_registry.get_provider("wikipedia")
        if wiki_p:
            try:
                res = wiki_p.search(query, limit=max_results)
                lat = (time.time() - t0) * 1000
                if res.success and res.data:
                    data_items = res.data if isinstance(res.data, list) else [res.data]
                    for item in data_items:
                        title = item.get("title", f"Wikipedia: {query}")
                        summary = item.get("summary", item.get("snippet", ""))
                        url = item.get("full_url", item.get("url", f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}"))

                        if summary or title:
                            results.append(KnowledgeResult(
                                provider="wikipedia",
                                source_type=SourceType.WIKIPEDIA,
                                title=title,
                                content=summary or title,
                                summary=summary[:200] + "..." if len(summary) > 200 else summary,
                                url=url,
                                confidence=0.85,
                                latency_ms=lat,
                                metadata={"url": url},
                            ))
                    logger.info(f"WikipediaKnowledgeAgent retrieved {len(results)} items in {int(lat)}ms")
            except Exception as e:
                logger.error(f"WikipediaKnowledgeAgent error: {e}", exc_info=True)

        return results
