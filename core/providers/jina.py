"""Jina AI Reader Provider Wrapper."""

import time
import requests
from typing import Dict, Any, Optional
from core.config import Config, mask_api_key
from core.providers.base import BaseProvider, ProviderCategory, ProviderResponse, ProviderStatus


class JinaProvider(BaseProvider):
    """Jina AI Reader Provider integration wrapper."""

    def __init__(self):
        super().__init__(name="jina", category=ProviderCategory.READER, is_optional=True)
        self.api_key = Config.JINA_API_KEY

    def initialize(self) -> bool:
        if not self.api_key:
            self.last_error = "JINA_API_KEY is missing."
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
            data={"configured": True, "engine": "Jina AI Reader (r.jina.ai)"},
            metadata={"api_key_masked": mask_api_key(self.api_key)},
        )

    def fetch(self, identifier: str, **kwargs) -> ProviderResponse:
        """Extract clean markdown from URL using Jina AI Reader API."""
        t0 = time.time()
        url = identifier.strip()
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        jina_endpoint = f"https://r.jina.ai/{url}"
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            resp = requests.get(jina_endpoint, headers=headers, timeout=10.0)
            latency = round((time.time() - t0) * 1000, 2)
            if resp.status_code == 200:
                content_type = resp.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    data = resp.json()
                else:
                    data = {"url": url, "content": resp.text}

                return ProviderResponse(
                    success=True,
                    provider=self.name,
                    category=self.category,
                    status=ProviderStatus.AVAILABLE.value,
                    latency_ms=latency,
                    data=data,
                    metadata={"url": url},
                )
            else:
                return ProviderResponse(
                    success=False,
                    provider=self.name,
                    category=self.category,
                    status=ProviderStatus.ERROR.value,
                    latency_ms=latency,
                    error=f"Jina AI Reader returned HTTP {resp.status_code}: {resp.text[:200]}",
                )
        except Exception as err:
            latency = round((time.time() - t0) * 1000, 2)
            return ProviderResponse(
                success=False,
                provider=self.name,
                category=self.category,
                status=ProviderStatus.ERROR.value,
                latency_ms=latency,
                error=f"Jina AI Reader request failed: {str(err)}",
            )
