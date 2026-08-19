"""DuckDuckGo Search Provider Wrapper (Supporting native DDGS and SerpApi engine)."""

import time
from typing import List, Dict, Any
from core.config import Config, mask_api_key
from core.providers.base import BaseProvider, ProviderCategory, ProviderResponse, ProviderStatus


class DuckDuckGoProvider(BaseProvider):
    """DuckDuckGo Backup Web Search Provider integration wrapper."""

    def __init__(self):
        super().__init__(name="duckduckgo", category=ProviderCategory.SEARCH, is_optional=True)
        self.enabled = Config.DUCKDUCKGO_ENABLED
        self.serpapi_key = Config.SERPAPI_API_KEY

    def initialize(self) -> bool:
        if not self.enabled:
            self.last_error = "DUCKDUCKGO_ENABLED is set to False."
            self.is_initialized = False
            return False
        self.is_initialized = True
        return True

    def health_check(self) -> ProviderResponse:
        t0 = time.time()
        if not self.initialize():
            return ProviderResponse(
                success=False,
                provider=self.name,
                category=self.category,
                status=ProviderStatus.NOT_CONFIGURED.value,
                error=self.last_error,
            )
        latency = round((time.time() - t0) * 1000, 2)
        engine_type = "SerpApi (DuckDuckGo)" if self.serpapi_key else "duckduckgo-search (Native)"
        return ProviderResponse(
            success=True,
            provider=self.name,
            category=self.category,
            status=ProviderStatus.READY.value,
            latency_ms=latency,
            data={"engine": engine_type, "configured": True},
            metadata={"serpapi_key_masked": mask_api_key(self.serpapi_key)},
        )

    def search(self, query: str, max_results: int = 5, **kwargs) -> ProviderResponse:
        t0 = time.time()
        if not self.is_initialized and not self.initialize():
            return ProviderResponse(
                success=False,
                provider=self.name,
                category=self.category,
                status=ProviderStatus.NOT_CONFIGURED.value,
                error="DuckDuckGo provider is disabled.",
            )

        # 1. Try SerpApi DuckDuckGo engine if key is configured
        if self.serpapi_key:
            try:
                import serpapi
                client = serpapi.Client(api_key=self.serpapi_key)
                res = client.search({
                    "engine": "duckduckgo",
                    "q": query,
                    "kl": kwargs.get("kl", "us-en")
                })
                organic = res.get("organic_results", [])
                parsed = [
                    {"title": item.get("title", ""), "link": item.get("link", ""), "snippet": item.get("snippet", "")}
                    for item in organic[:max_results]
                ]
                latency = round((time.time() - t0) * 1000, 2)
                return ProviderResponse(
                    success=True,
                    provider=self.name,
                    category=self.category,
                    status=ProviderStatus.AVAILABLE.value,
                    latency_ms=latency,
                    data=parsed,
                    metadata={"source": "serpapi", "count": len(parsed)},
                )
            except Exception as serp_err:
                # Fallback to native ddgs if serpapi fails
                pass

        # 2. Fallback to native duckduckgo_search
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                ddg_results = list(ddgs.text(query, max_results=max_results))
            parsed = [
                {"title": r.get("title", ""), "link": r.get("href", r.get("link", "")), "snippet": r.get("body", r.get("snippet", ""))}
                for r in ddg_results
            ]
            latency = round((time.time() - t0) * 1000, 2)
            return ProviderResponse(
                success=True,
                provider=self.name,
                category=self.category,
                status=ProviderStatus.AVAILABLE.value,
                latency_ms=latency,
                data=parsed,
                metadata={"source": "duckduckgo_search", "count": len(parsed)},
            )
        except Exception as ddg_err:
            latency = round((time.time() - t0) * 1000, 2)
            return ProviderResponse(
                success=False,
                provider=self.name,
                category=self.category,
                status=ProviderStatus.ERROR.value,
                latency_ms=latency,
                error=f"DuckDuckGo search failed: {str(ddg_err)}",
            )
