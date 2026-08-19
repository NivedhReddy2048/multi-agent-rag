"""GitHub Repository Provider Wrapper."""

import time
import requests
from typing import List, Dict, Any
from core.config import Config, mask_api_key
from core.providers.base import BaseProvider, ProviderCategory, ProviderResponse, ProviderStatus


class GithubProvider(BaseProvider):
    """GitHub API Repository Provider integration wrapper."""

    def __init__(self):
        super().__init__(name="github", category=ProviderCategory.REPOSITORY, is_optional=True)
        self.api_key = Config.GITHUB_TOKEN
        self.base_url = "https://api.github.com/search/repositories"

    def initialize(self) -> bool:
        if not self.api_key:
            self.last_error = "GITHUB_TOKEN is missing."
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
            data={"configured": True, "engine": "GitHub REST API v3"},
            metadata={"api_key_masked": mask_api_key(self.api_key)},
        )

    def search(self, query: str, max_results: int = 5, **kwargs) -> ProviderResponse:
        t0 = time.time()
        headers = {"Accept": "application/vnd.github+json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        params = {"q": query, "per_page": max_results}

        try:
            resp = requests.get(self.base_url, params=params, headers=headers, timeout=10.0)
            latency = round((time.time() - t0) * 1000, 2)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                parsed = [
                    {
                        "full_name": repo.get("full_name", ""),
                        "description": repo.get("description", ""),
                        "html_url": repo.get("html_url", ""),
                        "stars": repo.get("stargazers_count", 0),
                        "language": repo.get("language", ""),
                    }
                    for repo in items
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
                    error=f"GitHub API returned HTTP {resp.status_code}: {resp.text[:200]}",
                )
        except Exception as err:
            latency = round((time.time() - t0) * 1000, 2)
            return ProviderResponse(
                success=False,
                provider=self.name,
                category=self.category,
                status=ProviderStatus.ERROR.value,
                latency_ms=latency,
                error=f"GitHub search failed: {str(err)}",
            )
