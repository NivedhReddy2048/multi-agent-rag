"""Centralized Provider Registry for EKIP Knowledge Providers."""

from typing import Dict, List, Optional, Any
from core.logger import get_logger
from core.providers.base import BaseProvider, ProviderResponse
from core.providers.gemini import GeminiProvider
from core.providers.groq import GroqProvider
from core.providers.cohere import CohereProvider
from core.providers.mistral import MistralProvider
from core.providers.tavily import TavilyProvider
from core.providers.duckduckgo import DuckDuckGoProvider
from core.providers.firecrawl import FirecrawlProvider
from core.providers.jina import JinaProvider
from core.providers.semantic_scholar import SemanticScholarProvider
from core.providers.wikipedia import WikipediaProvider
from core.providers.arxiv import ArxivProvider
from core.providers.youtube import YoutubeProvider
from core.providers.google_books import GoogleBooksProvider
from core.providers.github import GithubProvider

logger = get_logger("core.providers.registry")


class ProviderRegistry:
    """Registry managing lifecycle and diagnostics for all 14 EKIP providers."""

    def __init__(self):
        self._providers: Dict[str, BaseProvider] = {}
        self._register_all_providers()

    def _register_all_providers(self):
        providers_list: List[BaseProvider] = [
            GeminiProvider(),
            GroqProvider(),
            CohereProvider(),
            MistralProvider(),
            TavilyProvider(),
            DuckDuckGoProvider(),
            FirecrawlProvider(),
            JinaProvider(),
            SemanticScholarProvider(),
            WikipediaProvider(),
            ArxivProvider(),
            YoutubeProvider(),
            GoogleBooksProvider(),
            GithubProvider(),
        ]
        for p in providers_list:
            self._providers[p.name.lower()] = p

    def get_provider(self, name: str) -> Optional[BaseProvider]:
        """Retrieve provider instance by name."""
        return self._providers.get(name.lower())

    def list_providers(self) -> List[BaseProvider]:
        """List all registered providers."""
        return list(self._providers.values())

    def run_all_health_checks(self) -> Dict[str, ProviderResponse]:
        """Execute health checks for all registered providers."""
        reports: Dict[str, ProviderResponse] = {}
        for name, provider in self._providers.items():
            try:
                report = provider.health_check()
                reports[name] = report
            except Exception as err:
                logger.error(f"Health check failed for provider '{name}': {err}")
                reports[name] = ProviderResponse(
                    success=False,
                    provider=name,
                    category=provider.category,
                    status="Error",
                    error=str(err),
                )
        return reports

    def get_diagnostics_summary(self) -> Dict[str, Dict[str, Any]]:
        """Format summary dictionary for UI diagnostics."""
        summary = {}
        for name, provider in self._providers.items():
            report = provider.health_check()
            summary[name] = {
                "name": provider.name,
                "category": provider.category.value,
                "status": report.status,
                "success": report.success,
                "latency_ms": report.latency_ms,
                "error": report.error,
                "metadata": report.metadata,
            }
        return summary


# Global singleton instance for platform-wide access
provider_registry = ProviderRegistry()

__all__ = ["ProviderRegistry", "provider_registry"]
