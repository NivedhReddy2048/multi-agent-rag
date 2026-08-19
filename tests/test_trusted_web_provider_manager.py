"""Unit tests for TrustedWebProviderManager primary/fallback behavior."""

import pytest
from core.providers.base import BaseProvider, ProviderCategory, ProviderResponse, ProviderStatus
from core.providers.trusted_web import TrustedWebProviderManager, is_recoverable_failure
from core.events.event_bus import event_bus
from core.events.events import Event


class MockSearchProvider(BaseProvider):
    def __init__(self, name: str, should_succeed: bool = True, error_msg: str = "", data: list = None):
        super().__init__(name=name, category=ProviderCategory.SEARCH)
        self.should_succeed = should_succeed
        self.error_msg = error_msg
        self.data = data or [{"title": f"{name} Result", "snippet": "Sample text", "url": "https://example.com"}]

    def initialize(self) -> bool:
        return self.should_succeed

    def health_check(self) -> ProviderResponse:
        return ProviderResponse(
            success=self.should_succeed,
            provider=self.name,
            category=self.category,
            status=ProviderStatus.READY.value if self.should_succeed else ProviderStatus.ERROR.value,
        )

    def search(self, query: str, max_results: int = 5, **kwargs) -> ProviderResponse:
        if self.should_succeed:
            return ProviderResponse(
                success=True,
                provider=self.name,
                category=self.category,
                status=ProviderStatus.AVAILABLE.value,
                latency_ms=10.0,
                data=self.data,
            )
        return ProviderResponse(
            success=False,
            provider=self.name,
            category=self.category,
            status=ProviderStatus.ERROR.value,
            latency_ms=10.0,
            error=self.error_msg,
        )


def test_tavily_success():
    """Verify normal search returns Tavily results without triggering fallback."""
    tavily = MockSearchProvider("tavily", should_succeed=True)
    ddg = MockSearchProvider("duckduckgo", should_succeed=True)
    manager = TrustedWebProviderManager(primary_provider=tavily, fallback_provider=ddg)

    res = manager.search("quantum computing")
    assert res.success is True
    assert res.provider == "tavily"
    assert manager.primary_success_count == 1
    assert manager.fallback_count == 0


def test_tavily_quota_exceeded_fallback():
    """Verify Tavily 429 quota exhaustion triggers DuckDuckGo fallback."""
    tavily = MockSearchProvider("tavily", should_succeed=False, error_msg="HTTP 429 Rate Limit / Quota Exceeded")
    ddg = MockSearchProvider("duckduckgo", should_succeed=True)
    manager = TrustedWebProviderManager(primary_provider=tavily, fallback_provider=ddg)

    events_captured = []
    def event_handler(evt: Event):
        events_captured.append(evt.event_type)

    event_bus.subscribe("FallbackTriggered", event_handler)
    event_bus.subscribe("FallbackSuccess", event_handler)

    res = manager.search("machine learning")

    assert res.success is True
    assert res.provider == "duckduckgo"
    assert manager.fallback_count == 1
    assert manager.fallback_success_count == 1
    assert "FallbackTriggered" in events_captured
    assert "FallbackSuccess" in events_captured


def test_tavily_timeout_fallback():
    """Verify Tavily timeout triggers DuckDuckGo fallback."""
    tavily = MockSearchProvider("tavily", should_succeed=False, error_msg="Connection timed out after 10s")
    ddg = MockSearchProvider("duckduckgo", should_succeed=True)
    manager = TrustedWebProviderManager(primary_provider=tavily, fallback_provider=ddg)

    res = manager.search("deep learning")
    assert res.success is True
    assert res.provider == "duckduckgo"
    assert manager.fallback_count == 1


def test_tavily_auth_failure_fallback():
    """Verify Tavily 401/403 authentication failure triggers DuckDuckGo fallback."""
    tavily = MockSearchProvider("tavily", should_succeed=False, error_msg="TAVILY_API_KEY is missing or invalid 401 Unauthorized")
    ddg = MockSearchProvider("duckduckgo", should_succeed=True)
    manager = TrustedWebProviderManager(primary_provider=tavily, fallback_provider=ddg)

    res = manager.search("artificial intelligence")
    assert res.success is True
    assert res.provider == "duckduckgo"
    assert manager.fallback_count == 1


def test_invalid_query_no_fallback():
    """Verify empty or non-string invalid queries do NOT trigger fallback."""
    tavily = MockSearchProvider("tavily", should_succeed=True)
    ddg = MockSearchProvider("duckduckgo", should_succeed=True)
    manager = TrustedWebProviderManager(primary_provider=tavily, fallback_provider=ddg)

    with pytest.raises(ValueError, match="Invalid query"):
        manager.search("")

    with pytest.raises(ValueError, match="Invalid query"):
        manager.search("   ")

    assert manager.fallback_count == 0


def test_both_providers_unavailable():
    """Verify response when both primary and fallback providers fail."""
    tavily = MockSearchProvider("tavily", should_succeed=False, error_msg="Tavily 503 Server Error")
    ddg = MockSearchProvider("duckduckgo", should_succeed=False, error_msg="DuckDuckGo rate limit")
    manager = TrustedWebProviderManager(primary_provider=tavily, fallback_provider=ddg)

    res = manager.search("neural networks")
    assert res.success is False
    assert manager.fallback_count == 1
    assert manager.fallback_failure_count == 1
