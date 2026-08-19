"""Targeted unit tests for EKIP LLM Health & Diagnostics Page accuracy, provider configuration, and security."""

import pytest
from config.settings import Config
from core.config import EKIPConfig
from core.observability.health import (
    get_configured_providers,
    get_all_provider_health,
    get_provider_uptime_stats,
    get_token_usage_stats,
    get_failover_events,
    get_recent_telemetry,
    get_system_diagnostics,
)


def test_configured_providers_match_authoritative_runtime_config():
    """Verify that configured providers derive dynamically from Config.PROVIDER_PRIORITY."""
    providers = get_configured_providers()
    expected = [p.capitalize() for p in Config.PROVIDER_PRIORITY]
    assert providers == expected
    assert "Deepseek" not in providers
    assert "Openai" not in providers


def test_config_and_ekipconfig_zero_drift():
    """Verify Config and EKIPConfig return 100% identical results for all providers."""
    providers = ["groq", "gemini", "mistral", "cohere", "tavily", "github", "wikipedia", "duckduckgo"]
    for p in providers:
        assert Config.get_provider_key(p) == EKIPConfig.get_provider_key(p)
        assert Config.is_provider_configured(p) == EKIPConfig.is_provider_configured(p)
        assert Config.get_masked_key(p) == EKIPConfig.get_masked_key(p)


def test_get_all_provider_health_excludes_deepseek_and_openai():
    """Verify that get_all_provider_health returns only actual configured EKIP providers."""
    health_list = get_all_provider_health()
    provider_names = [h["provider"] for h in health_list]
    
    assert "Groq" in provider_names
    assert "Gemini" in provider_names
    assert "Mistral" in provider_names
    assert "Cohere" in provider_names
    assert "DeepSeek" not in provider_names
    assert "OpenAI" not in provider_names
    assert len(health_list) == len(Config.PROVIDER_PRIORITY)


def test_get_masked_key_exists_and_protects_secrets():
    """Verify that Config.get_masked_key returns safe masked status without raising AttributeError."""
    for provider in ["groq", "gemini", "mistral", "cohere", "tavily", "github", "wikipedia", "duckduckgo"]:
        masked = Config.get_masked_key(provider)
        assert isinstance(masked, str)
        key = Config.get_provider_key(provider)
        if key and len(key.strip()) > 8:
            raw_key = key.strip()
            assert raw_key not in masked, f"Raw secret key leaked for provider {provider}!"
            assert masked.startswith("Configured (")


def test_is_provider_configured():
    """Verify Config.is_provider_configured works for all standard and public providers."""
    assert Config.is_provider_configured("wikipedia") is True
    assert Config.is_provider_configured("arxiv") is True
    assert isinstance(Config.is_provider_configured("groq"), bool)
    assert isinstance(Config.is_provider_configured("gemini"), bool)


def test_uptime_and_token_stats_exclude_unconfigured_providers():
    """Verify that uptime and token stats only contain EKIP configured providers."""
    uptime = get_provider_uptime_stats()
    assert "DeepSeek" not in uptime
    assert "OpenAI" not in uptime
    assert "Groq" in uptime
    assert "Gemini" in uptime

    token_stats = get_token_usage_stats()
    for day_entry in token_stats:
        assert "DeepSeek" not in day_entry
        assert "OpenAI" not in day_entry
        assert "Groq" in day_entry
        assert "Gemini" in day_entry


def test_failover_events_no_fabricated_deepseek():
    """Verify that failover events contain no fake DeepSeek references."""
    events = get_failover_events()
    for ev in events:
        assert "DeepSeek" not in ev["event"]
        assert "DeepSeek" not in ev["reason"]


def test_get_recent_telemetry_graceful_handling():
    """Verify recent telemetry executes gracefully without error."""
    telemetry = get_recent_telemetry(limit=10)
    assert isinstance(telemetry, list)
    for entry in telemetry:
        assert "query" in entry
        assert "provider" in entry


def test_system_diagnostics_structure():
    """Verify system diagnostics metrics structure."""
    diag = get_system_diagnostics()
    assert "vector_store" in diag
    assert "memory" in diag
    assert "auth_db" in diag
    assert "chat_db" in diag
