"""Google Books API Provider Wrapper."""

import time
import requests
from typing import List, Dict, Any
from core.config import Config, mask_api_key
from core.providers.base import BaseProvider, ProviderCategory, ProviderResponse, ProviderStatus


class GoogleBooksProvider(BaseProvider):
    """Google Books Provider integration wrapper."""

    def __init__(self):
        super().__init__(name="google_books", category=ProviderCategory.BOOKS, is_optional=True)
        self.api_key = Config.GOOGLE_BOOKS_API_KEY
        self.base_url = "https://www.googleapis.com/books/v1/volumes"

    def initialize(self) -> bool:
        if not self.api_key:
            self.last_error = "GOOGLE_BOOKS_API_KEY is missing."
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
            data={"configured": True, "engine": "Google Books API v1"},
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
                error="Google Books API key missing.",
            )

        params = {
            "q": query,
            "maxResults": max_results,
            "key": self.api_key,
        }

        try:
            resp = requests.get(self.base_url, params=params, timeout=10.0)
            latency = round((time.time() - t0) * 1000, 2)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                parsed = [
                    {
                        "title": item.get("volumeInfo", {}).get("title", ""),
                        "authors": item.get("volumeInfo", {}).get("authors", []),
                        "publisher": item.get("volumeInfo", {}).get("publisher", ""),
                        "published_date": item.get("volumeInfo", {}).get("publishedDate", ""),
                        "description": item.get("volumeInfo", {}).get("description", "")[:300],
                        "preview_link": item.get("volumeInfo", {}).get("previewLink", ""),
                    }
                    for item in items
                ]
                return ProviderResponse(
                    success=True,
                    provider=self.name,
                    category=self.category,
                    status=ProviderStatus.AVAILABLE.value,
                    latency_ms=latency,
                    data=parsed,
                    metadata={"count": len(parsed)},
                )
            else:
                return ProviderResponse(
                    success=False,
                    provider=self.name,
                    category=self.category,
                    status=ProviderStatus.ERROR.value,
                    latency_ms=latency,
                    error=f"Google Books API returned HTTP {resp.status_code}: {resp.text[:200]}",
                )
        except Exception as err:
            latency = round((time.time() - t0) * 1000, 2)
            return ProviderResponse(
                success=False,
                provider=self.name,
                category=self.category,
                status=ProviderStatus.ERROR.value,
                latency_ms=latency,
                error=f"Google Books search failed: {str(err)}",
            )
