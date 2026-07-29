"""Web evidence retrieval used only when the orchestrator selects that branch."""

import hashlib
from typing import Dict, List
from urllib.parse import urlparse

from core.logger import get_logger

logger = get_logger("core.web_search")


def search_web(query: str, api_key: str, max_results: int = 3) -> List[Dict]:
    """Return normalized web evidence; this function makes no routing decisions."""
    if not api_key:
        logger.info("Web search skipped because TAVILY_API_KEY is not configured.")
        return []

    try:
        from tavily import TavilyClient

        response = TavilyClient(api_key=api_key).search(
            query, max_results=max_results, search_depth="advanced"
        )
        results = []
        for item in response.get("results", []):
            url = str(item.get("url", ""))
            title = str(item.get("title", "Web Result"))
            snippet = str(item.get("content", ""))
            domain = urlparse(url).netloc
            url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()[:8]
            results.append({
                "content": snippet,
                "snippet": snippet,
                "title": title,
                "url": url,
                "domain": domain,
                "source_file": f"🌐 {title}",
                "page": url[:120],
                "chunk_id": f"web_{url_hash}",
                "score": float(item.get("score", 0.85) or 0.85),
            })
        logger.info("Web search returned {} normalized results for query '{}'.", len(results), query[:80])
        return results
    except Exception as exc:
        logger.error("Web search failed without returning user-facing content: {}", type(exc).__name__)
        return []
