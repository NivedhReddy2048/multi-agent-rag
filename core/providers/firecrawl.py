"""Firecrawl Structured Web Extraction Provider Wrapper."""

import time
import requests
from typing import Dict, Any, Optional
from core.config import Config, mask_api_key
from core.providers.base import BaseProvider, ProviderCategory, ProviderResponse, ProviderStatus


class FirecrawlProvider(BaseProvider):
    """Firecrawl Web Scraping & Extraction Provider integration wrapper."""

    def __init__(self):
        super().__init__(name="firecrawl", category=ProviderCategory.EXTRACTION, is_optional=True)
        self.api_key = Config.FIRECRAWL_API_KEY

    def initialize(self) -> bool:
        if not self.api_key:
            self.last_error = "FIRECRAWL_API_KEY is missing."
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
            data={"configured": True, "engine": "Firecrawl Scraper API"},
            metadata={"api_key_masked": mask_api_key(self.api_key)},
        )

    def fetch(self, identifier: str, **kwargs) -> ProviderResponse:
        """Extract web content from a given URL."""
        t0 = time.time()
        if not self.is_initialized and not self.initialize():
            return ProviderResponse(
                success=False,
                provider=self.name,
                category=self.category,
                status=ProviderStatus.NOT_CONFIGURED.value,
                error="Firecrawl API key is missing.",
            )

        url = identifier
        try:
            # Attempt to use official firecrawl-py SDK if available
            try:
                from firecrawl import FirecrawlApp
                app = FirecrawlApp(api_key=self.api_key)
                scrape_result = app.scrape_url(url, params=kwargs.get("params", {'formats': ['markdown']}))
                latency = round((time.time() - t0) * 1000, 2)
                return ProviderResponse(
                    success=True,
                    provider=self.name,
                    category=self.category,
                    status=ProviderStatus.AVAILABLE.value,
                    latency_ms=latency,
                    data=scrape_result,
                    metadata={"url": url},
                )
            except ImportError:
                # Direct REST fallback
                headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
                resp = requests.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    json={"url": url, "formats": ["markdown"]},
                    headers=headers,
                    timeout=10.0,
                )
                latency = round((time.time() - t0) * 1000, 2)
                if resp.status_code == 200:
                    return ProviderResponse(
                        success=True,
                        provider=self.name,
                        category=self.category,
                        status=ProviderStatus.AVAILABLE.value,
                        latency_ms=latency,
                        data=resp.json(),
                        metadata={"url": url},
                    )
                else:
                    return ProviderResponse(
                        success=False,
                        provider=self.name,
                        category=self.category,
                        status=ProviderStatus.ERROR.value,
                        latency_ms=latency,
                        error=f"Firecrawl REST error HTTP {resp.status_code}: {resp.text[:200]}",
                    )
        except Exception as err:
            latency = round((time.time() - t0) * 1000, 2)
            return ProviderResponse(
                success=False,
                provider=self.name,
                category=self.category,
                status=ProviderStatus.ERROR.value,
                latency_ms=latency,
                error=f"Firecrawl extraction error: {str(err)}",
            )
