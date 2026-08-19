"""Semantic Scholar Academic Paper Search Provider Wrapper."""

import time
import requests
from typing import List, Dict, Any
from core.config import Config, mask_api_key
from core.providers.base import BaseProvider, ProviderCategory, ProviderResponse, ProviderStatus


class SemanticScholarProvider(BaseProvider):
    """Semantic Scholar Academic Literature Provider integration wrapper."""

    def __init__(self):
        super().__init__(name="semantic_scholar", category=ProviderCategory.ACADEMIC, is_optional=True)
        self.api_key = Config.SEMANTIC_SCHOLAR_API_KEY
        self.base_url = "https://api.semanticscholar.org/graph/v1/paper/search"

    def initialize(self) -> bool:
        if not self.api_key:
            self.last_error = "SEMANTIC_SCHOLAR_API_KEY is missing."
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
            data={"configured": True, "engine": "Semantic Scholar Academic Graph"},
            metadata={"api_key_masked": mask_api_key(self.api_key)},
        )

    def search(self, query: str, limit: int = 5, **kwargs) -> ProviderResponse:
        t0 = time.time()
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        params = {
            "query": query,
            "limit": limit,
            "fields": "title,authors,year,abstract,url,citationCount,venue",
        }

        try:
            resp = requests.get(self.base_url, params=params, headers=headers, timeout=10.0)
            latency = round((time.time() - t0) * 1000, 2)
            if resp.status_code == 200:
                papers = resp.json().get("data", [])
                parsed = [
                    {
                        "title": p.get("title", ""),
                        "authors": [a.get("name") for a in p.get("authors", [])],
                        "year": p.get("year"),
                        "abstract": p.get("abstract", ""),
                        "url": p.get("url", ""),
                        "venue": p.get("venue", ""),
                        "citations": p.get("citationCount", 0),
                    }
                    for p in papers
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
                    error=f"Semantic Scholar HTTP {resp.status_code}: {resp.text[:200]}",
                )
        except Exception as err:
            latency = round((time.time() - t0) * 1000, 2)
            return ProviderResponse(
                success=False,
                provider=self.name,
                category=self.category,
                status=ProviderStatus.ERROR.value,
                latency_ms=latency,
                error=f"Semantic Scholar search error: {str(err)}",
            )
