"""Semantic Scholar Knowledge Agent for Academic Research Papers."""

import time
from typing import List
from agents.sources.base_agent import BaseKnowledgeAgent
from core.models.domain import KnowledgeResult, SourceType
from core.providers import provider_registry
from core.logger import get_logger

logger = get_logger("agents.sources.semantic_scholar_agent")


class SemanticScholarKnowledgeAgent(BaseKnowledgeAgent):
    """Retrieves academic research papers from Semantic Scholar API."""

    def __init__(self):
        super().__init__(
            agent_name="SemanticScholarKnowledgeAgent",
            source_type=SourceType.SEMANTIC_SCHOLAR,
            provider_key="semantic_scholar"
        )

    def initialize(self) -> bool:
        self.is_initialized = True
        return True

    def health(self) -> bool:
        p = provider_registry.get_provider("semantic_scholar")
        return p is not None

    def execute(self, query: str, max_results: int = 5) -> List[KnowledgeResult]:
        t0 = time.time()
        results: List[KnowledgeResult] = []

        p = provider_registry.get_provider("semantic_scholar")
        if p:
            try:
                res = p.search(query, limit=max_results)
                lat = (time.time() - t0) * 1000
                if res.success and res.data:
                    raw_papers = res.data if isinstance(res.data, list) else res.data.get("papers", [])
                    for paper in raw_papers:
                        title = paper.get("title", "Research Paper")
                        abstract = paper.get("abstract", "") or paper.get("snippet", "No abstract available.")
                        authors = [a.get("name", "") if isinstance(a, dict) else str(a) for a in paper.get("authors", [])]
                        url = paper.get("url", paper.get("paper_url", ""))
                        year = str(paper.get("year", ""))

                        results.append(KnowledgeResult(
                            provider="semantic_scholar",
                            source_type=SourceType.SEMANTIC_SCHOLAR,
                            title=title,
                            content=abstract,
                            summary=abstract[:250] + "..." if len(abstract) > 250 else abstract,
                            url=url,
                            authors=authors,
                            published_date=year,
                            confidence=0.90,
                            latency_ms=lat,
                            metadata={
                                "citationCount": paper.get("citationCount", 0),
                                "paperId": paper.get("paperId", ""),
                            },
                        ))
                    logger.info(f"SemanticScholarKnowledgeAgent retrieved {len(results)} papers in {int(lat)}ms")
            except Exception as e:
                logger.error(f"SemanticScholarKnowledgeAgent error: {e}", exc_info=True)

        return results
