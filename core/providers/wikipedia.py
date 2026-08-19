"""Wikipedia Open Reference Provider Wrapper (No API Key Required)."""

import time
import requests
from typing import List, Dict, Any
from core.providers.base import BaseProvider, ProviderCategory, ProviderResponse, ProviderStatus


class WikipediaProvider(BaseProvider):
    """Wikipedia Reference Provider integration wrapper (Public Open API)."""

    def __init__(self):
        super().__init__(name="wikipedia", category=ProviderCategory.ACADEMIC, is_optional=False)

    def initialize(self) -> bool:
        self.is_initialized = True
        return True

    def health_check(self) -> ProviderResponse:
        t0 = time.time()
        self.initialize()
        latency = round((time.time() - t0) * 1000, 2)
        return ProviderResponse(
            success=True,
            provider=self.name,
            category=self.category,
            status=ProviderStatus.READY.value,
            latency_ms=latency,
            data={"configured": True, "type": "Public Open API (No API Key Required)"},
            metadata={"public": True},
        )

    def search(self, query: str, limit: int = 5, **kwargs) -> ProviderResponse:
        t0 = time.time()
        # 1. Try official wikipediaapi package
        try:
            import wikipediaapi
            wiki = wikipediaapi.Wikipedia(
                user_agent="EKIP/2.1 Educational Knowledge Engine (contact@ekip.edu)",
                language="en"
            )
            page = wiki.page(query)
            if page.exists():
                latency = round((time.time() - t0) * 1000, 2)
                data = [{
                    "title": page.title,
                    "summary": page.summary[:1000],
                    "full_url": page.fullurl,
                    "sections": [s.title for s in page.sections[:5]],
                }]
                return ProviderResponse(
                    success=True,
                    provider=self.name,
                    category=self.category,
                    status=ProviderStatus.AVAILABLE.value,
                    latency_ms=latency,
                    data=data,
                    metadata={"source": "wikipedia-api", "count": 1},
                )
        except Exception:
            pass

        # 2. Fallback to MediaWiki REST search endpoint
        try:
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": limit,
            }
            resp = requests.get(url, params=params, headers={"User-Agent": "EKIP/2.1"}, timeout=8.0)
            latency = round((time.time() - t0) * 1000, 2)
            if resp.status_code == 200:
                raw_results = resp.json().get("query", {}).get("search", [])
                parsed = [
                    {
                        "title": r.get("title", ""),
                        "snippet": r.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", ""),
                        "pageid": r.get("pageid"),
                        "url": f"https://en.wikipedia.org/wiki/{r.get('title', '').replace(' ', '_')}"
                    }
                    for r in raw_results
                ]
                return ProviderResponse(
                    success=True,
                    provider=self.name,
                    category=self.category,
                    status=ProviderStatus.AVAILABLE.value,
                    latency_ms=latency,
                    data=parsed,
                    metadata={"source": "mediawiki_rest", "count": len(parsed)},
                )
            else:
                return ProviderResponse(
                    success=False,
                    provider=self.name,
                    category=self.category,
                    status=ProviderStatus.ERROR.value,
                    latency_ms=latency,
                    error=f"Wikipedia API HTTP {resp.status_code}",
                )
        except Exception as err:
            latency = round((time.time() - t0) * 1000, 2)
            return ProviderResponse(
                success=False,
                provider=self.name,
                category=self.category,
                status=ProviderStatus.ERROR.value,
                latency_ms=latency,
                error=f"Wikipedia search failed: {str(err)}",
            )
