"""Provider Registry for Multi-LLM Layer."""

from typing import Dict, List, Optional
from .base_provider import BaseLLMProvider
from .gemini_provider import GeminiProvider
from .groq_provider import GroqProvider
from .cohere_provider import CohereProvider
from .mistral_provider import MistralProvider
from core.logger import get_logger

logger = get_logger("core.llm.provider_registry")


class ProviderRegistry:
    """Registry maintaining initialized provider instances."""

    def __init__(self, config=None):
        from config.settings import Config
        cfg = config or Config

        self.providers: Dict[str, BaseLLMProvider] = {
            "gemini": GeminiProvider(cfg.GEMINI_MODEL, cfg.GEMINI_FALLBACK_MODEL, cfg.GEMINI_API_KEY),
            "groq": GroqProvider(cfg.GROQ_MODEL, cfg.GROQ_FALLBACK_MODEL, cfg.GROQ_API_KEY),
            "cohere": CohereProvider(cfg.COHERE_MODEL, cfg.COHERE_FALLBACK_MODEL, cfg.COHERE_API_KEY),
            "mistral": MistralProvider(cfg.MISTRAL_MODEL, cfg.MISTRAL_FALLBACK_MODEL, cfg.MISTRAL_API_KEY),
        }

        self.priority_order: List[str] = getattr(cfg, "PROVIDER_PRIORITY", ["groq", "gemini", "mistral", "cohere"])
        logger.info(f"ProviderRegistry initialized with priority order: {self.priority_order}")

    def get_provider(self, name: str) -> Optional[BaseLLMProvider]:
        return self.providers.get(name.lower())

    def get_ordered_providers(self) -> List[BaseLLMProvider]:
        ordered = []
        for name in self.priority_order:
            if name in self.providers:
                ordered.append(self.providers[name])
        return ordered
