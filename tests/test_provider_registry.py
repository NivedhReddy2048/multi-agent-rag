"""Unit and Integration Audit Tests for EKIP Phase 2.1 Provider Registry."""

import pytest
from core.config import Config, mask_api_key
from core.providers import provider_registry, ProviderStatus, ProviderCategory, ProviderResponse


def test_config_key_masking():
    """Verify key masking never exposes raw secret strings."""
    secret = "AIzaSyAl0U5gT44EbygUIiZUSuzHxVTu2EdNwMA"
    masked = mask_api_key(secret)
    assert secret not in masked or len(secret) < 10
    assert masked.startswith("AIza")
    assert masked.endswith("wMA")
    assert "..." in masked


def test_registry_initialization():
    """Verify all 14 providers are registered in singleton registry."""
    providers = provider_registry.list_providers()
    assert len(providers) == 14

    expected_names = {
        "gemini", "groq", "cohere", "mistral",
        "tavily", "duckduckgo", "firecrawl", "jina",
        "semantic_scholar", "wikipedia", "arxiv",
        "youtube", "google_books", "github"
    }
    registered_names = {p.name.lower() for p in providers}
    assert registered_names == expected_names


def test_open_apis_no_key_required():
    """Verify Wikipedia and arXiv operate as open APIs without requiring API keys."""
    wiki_p = provider_registry.get_provider("wikipedia")
    arxiv_p = provider_registry.get_provider("arxiv")

    assert wiki_p is not None
    assert arxiv_p is not None

    wiki_report = wiki_p.health_check()
    arxiv_report = arxiv_p.health_check()

    assert wiki_report.success is True
    assert wiki_report.status == ProviderStatus.READY.value

    assert arxiv_report.success is True
    assert arxiv_report.status == ProviderStatus.READY.value


def test_all_providers_health_checks():
    """Verify all 14 providers execute health checks gracefully returning ProviderResponse."""
    reports = provider_registry.run_all_health_checks()
    assert len(reports) == 14

    for name, report in reports.items():
        assert isinstance(report, ProviderResponse)
        assert report.provider == name
        assert report.status in [
            ProviderStatus.READY.value,
            ProviderStatus.AVAILABLE.value,
            ProviderStatus.CONFIGURED.value,
            ProviderStatus.NOT_CONFIGURED.value,
            ProviderStatus.ERROR.value,
        ]


def test_provider_search_graceful_response():
    """Verify provider search returns structured ProviderResponse without raising exceptions."""
    duck_p = provider_registry.get_provider("duckduckgo")
    res = duck_p.search("Python programming language")
    assert isinstance(res, ProviderResponse)
    assert res.provider == "duckduckgo"
    assert res.category == ProviderCategory.SEARCH


def test_provider_fetch_graceful_response():
    """Verify provider fetch returns structured ProviderResponse without raising exceptions."""
    jina_p = provider_registry.get_provider("jina")
    res = jina_p.fetch("https://example.com")
    assert isinstance(res, ProviderResponse)
    assert res.provider == "jina"
    assert res.category == ProviderCategory.READER
