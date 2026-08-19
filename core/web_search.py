"""Web evidence retrieval used only when the orchestrator selects that branch."""

import hashlib
from typing import Dict, List
from urllib.parse import urlparse
from core.providers.trusted_web import trusted_web_provider_manager
from core.logger import get_logger

logger = get_logger("core.web_search")


def search_web(query: str, api_key: str, max_results: int = 3) -> List[Dict]:
    """Return normalized web evidence using TrustedWebProviderManager."""
    if not query or not query.strip():
        logger.info("Web search skipped because query is empty.")
        return []

    try:
        res = trusted_web_provider_manager.search(query, max_results=max_results)
        results = []
        if res.success and res.data:
            raw_items = res.data if isinstance(res.data, list) else res.data.get("results", [])
            for item in raw_items:
                url = str(item.get("url", item.get("link", item.get("href", ""))))
                title = str(item.get("title", "Web Result"))
                snippet = str(item.get("content", item.get("snippet", item.get("body", ""))))
                domain = urlparse(url).netloc if url else "web"
                url_hash = hashlib.md5((url or title).encode("utf-8")).hexdigest()[:8]
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

