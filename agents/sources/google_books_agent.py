"""Google Books Knowledge Agent for Textbook & Literature Recommendations."""

import time
from typing import List
from agents.sources.base_agent import BaseKnowledgeAgent
from core.models.domain import KnowledgeResult, SourceType
from core.providers import provider_registry
from core.logger import get_logger

logger = get_logger("agents.sources.google_books_agent")


class GoogleBooksKnowledgeAgent(BaseKnowledgeAgent):
    """Retrieves book publications and textbook previews from Google Books API."""

    def __init__(self):
        super().__init__(
            agent_name="GoogleBooksKnowledgeAgent",
            source_type=SourceType.BOOK,
            provider_key="google_books"
        )

    def initialize(self) -> bool:
        self.is_initialized = True
        return True

    def health(self) -> bool:
        p = provider_registry.get_provider("google_books")
        return p is not None

    def execute(self, query: str, max_results: int = 5) -> List[KnowledgeResult]:
        t0 = time.time()
        results: List[KnowledgeResult] = []

        p = provider_registry.get_provider("google_books")
        if p:
            try:
                res = p.search(query, max_results=max_results)
                lat = (time.time() - t0) * 1000
                if res.success and res.data:
                    raw_items = res.data if isinstance(res.data, list) else res.data.get("items", [])
                    for item in raw_items:
                        info = item.get("volumeInfo", item)
                        title = info.get("title", "Book Title")
                        desc = info.get("description", info.get("snippet", "No description provided."))
                        authors = info.get("authors", [])
                        pub_date = info.get("publishedDate", "")
                        preview = info.get("previewLink", info.get("infoLink", info.get("url", "")))

                        results.append(KnowledgeResult(
                            provider="google_books",
                            source_type=SourceType.BOOK,
                            title=f"Book: {title}",
                            content=desc,
                            summary=desc[:200] + "..." if len(desc) > 200 else desc,
                            url=preview,
                            authors=authors if isinstance(authors, list) else [str(authors)],
                            published_date=pub_date,
                            confidence=0.85,
                            latency_ms=lat,
                            metadata={"publisher": info.get("publisher", ""), "preview_link": preview},
                        ))
                    logger.info(f"GoogleBooksKnowledgeAgent retrieved {len(results)} books in {int(lat)}ms")
            except Exception as e:
                logger.error(f"GoogleBooksKnowledgeAgent error: {e}", exc_info=True)

        return results
