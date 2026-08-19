"""Centralized Configuration Module for EKIP Platform.

Responsibilities:
- Load environment variables securely.
- Validate required primary keys (e.g. at least one valid LLM provider).
- Expose typed configuration for both legacy and Phase 2 knowledge providers.
- Support optional providers with safe fallback defaults.
- Key masking utilities for diagnostics & logging security.
"""

import os
from typing import Dict, Any, Optional
from config.settings import Config as RootConfig


def mask_api_key(key: str, visible_chars: int = 4) -> str:
    """Safely mask API key for logging and UI display."""
    if not key:
        return "NOT_CONFIGURED"
    if len(key) <= visible_chars * 2:
        return f"{key[:2]}***{key[-2:]}"
    return f"{key[:visible_chars]}...{key[-visible_chars:]}"


class EKIPConfig(RootConfig):
    """Centralized Typed Configuration Manager."""

    DUCKDUCKGO_ENABLED: bool = getattr(RootConfig, "DUCKDUCKGO_ENABLED", True)
    DUCKDUCKGO_REGION: str = getattr(RootConfig, "DUCKDUCKGO_REGION", "us-en")
    DUCKDUCKGO_MAX_RESULTS: int = getattr(RootConfig, "DUCKDUCKGO_MAX_RESULTS", 5)
    DUCKDUCKGO_TIMEOUT: int = getattr(RootConfig, "DUCKDUCKGO_TIMEOUT", 10)
    TAVILY_MAX_RESULTS: int = getattr(RootConfig, "TAVILY_MAX_RESULTS", 5)
    TAVILY_TIMEOUT: int = getattr(RootConfig, "TAVILY_TIMEOUT", 10)

    @classmethod
    def get_provider_key(cls, provider_name: str) -> Optional[str]:
        """Get API key for provider by string identifier."""
        return RootConfig.get_provider_key(provider_name)

    @classmethod
    def is_provider_configured(cls, provider_name: str) -> bool:
        """Check if provider credentials/settings are present."""
        return RootConfig.is_provider_configured(provider_name)

    @classmethod
    def get_masked_key(cls, provider_name: str) -> str:
        """Return masked key representation for diagnostics."""
        return RootConfig.get_masked_key(provider_name)


# Alias for backward compatibility & seamless importing
Config = EKIPConfig

__all__ = ["Config", "EKIPConfig", "mask_api_key"]
