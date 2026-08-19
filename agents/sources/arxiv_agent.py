"""arXiv Knowledge Agent for Open Academic Preprints."""

import time
from typing import List
from agents.sources.base_agent import BaseKnowledgeAgent
from core.models.domain import KnowledgeResult, SourceType
from core.providers import provider_registry
from core.logger import get_logger

logger = get_logger("agents.sources.arxiv_agent")


class ArxivKnowledgeAgent(BaseKnowledgeAgent):
    """Retrieves computer science, AI, and scientific preprints from arXiv API."""

    def __init__(self):
        super().__init__(
            agent_name="ArxivKnowledgeAgent",
            source_type=SourceType.ARXIV,
            provider_key="arxiv"
        )

    def initialize(self) -> bool:
        self.is_initialized = True
        return True

    def health(self) -> bool:
        p = provider_registry.get_provider("arxiv")
        return p is not None

    def execute(self, query: str, max_results: int = 5) -> List[KnowledgeResult]:
        t0 = time.time()
        results: List[KnowledgeResult] = []

        p = provider_registry.get_provider("arxiv")
        if p:
            try:
                res = p.search(query, max_results=max_results)
                lat = (time.time() - t0) * 1000
                if res.success and res.data:
                    raw_papers = res.data if isinstance(res.data, list) else res.data.get("papers", [])
                    for paper in raw_papers:
                        title = paper.get("title", "arXiv Preprint")
                        summary = paper.get("summary", paper.get("abstract", ""))
                        pdf_url = paper.get("pdf_url", paper.get("url", ""))
                        authors = paper.get("authors", [])
                        published = paper.get("published", "")

                        results.append(KnowledgeResult(
                            provider="arxiv",
                            source_type=SourceType.ARXIV,
                            title=f"arXiv: {title}",
                            content=summary,
                            summary=summary[:250] + "..." if len(summary) > 250 else summary,
                            url=pdf_url,
                            authors=authors if isinstance(authors, list) else [str(authors)],
                            published_date=published[:10] if published else None,
                            confidence=0.90,
                            latency_ms=lat,
                            metadata={"arxiv_id": paper.get("arxiv_id", ""), "pdf_url": pdf_url},
                        ))
                    logger.info(f"ArxivKnowledgeAgent retrieved {len(results)} preprints in {int(lat)}ms")
            except Exception as e:
                logger.error(f"ArxivKnowledgeAgent error: {e}", exc_info=True)

        return results
