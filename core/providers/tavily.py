"""Tavily Web Search Provider Wrapper."""

import time
from typing import Dict, Any, List
from core.config import Config, mask_api_key
from core.providers.base import BaseProvider, ProviderCategory, ProviderResponse, ProviderStatus


class TavilyProvider(BaseProvider):
    """Tavily Search API Provider integration wrapper."""

    def __init__(self):
        super().__init__(name="tavily", category=ProviderCategory.SEARCH, is_optional=True)
        self.api_key = Config.TAVILY_API_KEY

    def initialize(self) -> bool:
        if not self.api_key:
            self.last_error = "TAVILY_API_KEY is missing."
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
                metadata={"api_key_masked": mask_api_key(self.api_key)},
            )
        latency = round((time.time() - t0) * 1000, 2)
        return ProviderResponse(
            success=True,
            provider=self.name,
            category=self.category,
            status=ProviderStatus.READY.value,
            latency_ms=latency,
            data={"configured": True, "engine": "Tavily Search API"},
            metadata={"api_key_masked": mask_api_key(self.api_key)},
        )

    def search(self, query: str, max_results: int = 5, **kwargs) -> ProviderResponse:
        t0 = time.time()
        if not self.is_initialized and not self.initialize():
            return ProviderResponse(
                success=False,
                provider=self.name,
                category=self.category,
                status=ProviderStatus.NOT_CONFIGURED.value,
                error="Tavily API key is not configured.",
            )

        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=self.api_key)
            response = client.search(query=query, max_results=max_results)
            latency = round((time.time() - t0) * 1000, 2)
            results = response.get("results", [])
            return ProviderResponse(
                success=True,
                provider=self.name,
                category=self.category,
                status=ProviderStatus.AVAILABLE.value,
                latency_ms=latency,
                data=results,
                metadata={"count": len(results)},
            )
        except Exception as e:
            latency = round((time.time() - t0) * 1000, 2)
            return ProviderResponse(
                success=False,
                provider=self.name,
                category=self.category,
                status=ProviderStatus.ERROR.value,
                latency_ms=latency,
                error=f"Tavily search failed: {str(e)}",
            )
