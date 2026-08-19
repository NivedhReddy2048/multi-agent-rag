"""Groq LLM Provider Wrapper."""

import time
from core.config import Config, mask_api_key
from core.providers.base import BaseProvider, ProviderCategory, ProviderResponse, ProviderStatus


class GroqProvider(BaseProvider):
    """Groq LLM Provider integration wrapper."""

    def __init__(self):
        super().__init__(name="groq", category=ProviderCategory.LLM, is_optional=True)
        self.api_key = Config.GROQ_API_KEY
        self.primary_model = Config.GROQ_MODEL

    def initialize(self) -> bool:
        if not self.api_key:
            self.last_error = "GROQ_API_KEY is missing."
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
            data={"model": self.primary_model, "configured": True},
            metadata={"api_key_masked": mask_api_key(self.api_key)},
        )
