"""Trusted Web Provider Manager implementing resilient Tavily primary with DuckDuckGo fallback."""

import time
from typing import Dict, Any, Optional, List
from core.config import Config
from core.providers.base import BaseProvider, ProviderCategory, ProviderResponse, ProviderStatus
from core.providers.tavily import TavilyProvider
from core.providers.duckduckgo import DuckDuckGoProvider
from core.events.event_bus import event_bus
from core.events.events import Event, ProviderFailure
from core.reliability.health_monitor import health_monitor
from core.logger import get_logger

logger = get_logger("core.providers.trusted_web")


def is_recoverable_failure(error_msg: str, exc: Optional[Exception] = None) -> bool:
    """Classify whether a primary search failure is recoverable and eligible for fallback.
    
    Recoverable failures:
    - Quota/token exhaustion (e.g. HTTP 429, 'quota', 'rate limit', 'token limit', 'exceeded')
    - Authentication failures where fallback is appropriate (HTTP 401, 403, missing key, invalid key)
    - Connection/Network failures (socket, urllib, requests errors)
    - Request timeouts (TimeoutError, requests.exceptions.Timeout)
    - Temporary server errors (HTTP 5xx, 500, 502, 503, 504)
    - General unhandled network/API errors
    
    Non-recoverable failures (do NOT fallback):
    - Invalid query (e.g. empty or non-string query, invalid syntax)
    - Validation errors (e.g. ValueError, TypeError for inputs)
    - Empty requests
    - Internal programming errors (e.g. KeyError, NameError, AttributeError inside logic)
    """
    if exc:
        if isinstance(exc, (ValueError, TypeError, KeyError, AttributeError, NameError)):
            msg = str(exc).lower()
            if "invalid query" in msg or "validation" in msg or "empty" in msg or "non-string" in msg:
                return False

    err_lower = error_msg.lower() if error_msg else ""
    if "invalid query" in err_lower or "validation error" in err_lower or "empty request" in err_lower or "cannot be empty" in err_lower:
        return False

    return True


class TrustedWebProviderManager:
    """Manager providing resilient Trusted Web search with Tavily primary and DuckDuckGo fallback."""

    def __init__(
        self,
        primary_provider: Optional[BaseProvider] = None,
        fallback_provider: Optional[BaseProvider] = None,
    ):
        self.primary_provider = primary_provider or TavilyProvider()
        self.fallback_provider = fallback_provider or DuckDuckGoProvider()
        self.fallback_count: int = 0
        self.primary_success_count: int = 0
        self.fallback_success_count: int = 0
        self.fallback_failure_count: int = 0

    def health(self) -> bool:
        """Check health of trusted web subsystem."""
        primary_report = self.primary_provider.health_check()
        if primary_report.success:
            return True
        fallback_report = self.fallback_provider.health_check()
        return fallback_report.success

    def search(self, query: str, max_results: int = 5, **kwargs) -> ProviderResponse:
        """Execute web search with Tavily primary and automatic DuckDuckGo fallback."""
        if not query or not isinstance(query, str) or not query.strip():
            err = "Invalid query: Search query cannot be empty or non-string."
            logger.warning(f"TrustedWebProviderManager rejected request: {err}")
            raise ValueError(err)

        t0 = time.time()

        # 1. Primary provider selected event
        event_bus.publish(
            Event(
                event_type="PrimaryProviderSelected",
                payload={"provider": "tavily", "query": query},
            )
        )

        primary_failed = False
        primary_error_msg = ""
        primary_exc: Optional[Exception] = None
        tavily_response: Optional[ProviderResponse] = None

        # 2. Try Primary Provider (Tavily)
        try:
            tavily_response = self.primary_provider.search(query, max_results=max_results, **kwargs)
            if tavily_response and tavily_response.success:
                lat = round((time.time() - t0) * 1000, 2)
                self.primary_success_count += 1
                health_monitor.record_call("tavily", success=True, latency_ms=lat)
                return tavily_response
            else:
                primary_failed = True
                primary_error_msg = tavily_response.error if tavily_response else "Tavily returned unsuccessful response"
        except Exception as exc:
            primary_failed = True
            primary_exc = exc
            primary_error_msg = str(exc)

        # 3. If primary failed, check if failure is recoverable
        if primary_failed:
            lat_prim = round((time.time() - t0) * 1000, 2)
            health_monitor.record_call("tavily", success=False, latency_ms=lat_prim)
            event_bus.publish(
                ProviderFailure(
                    payload={"provider": "tavily", "error": primary_error_msg, "latency_ms": lat_prim}
                )
            )

            recoverable = is_recoverable_failure(primary_error_msg, primary_exc)

            if not recoverable:
                logger.warning(f"Tavily failed with non-recoverable error ({primary_error_msg}). Fallback disabled.")
                if tavily_response:
                    return tavily_response
                return ProviderResponse(
                    success=False,
                    provider="tavily",
                    category=ProviderCategory.SEARCH,
                    status=ProviderStatus.ERROR.value,
                    latency_ms=lat_prim,
                    error=primary_error_msg,
                )

            # 4. Trigger Fallback
            self.fallback_count += 1
            logger.info(f"Tavily search failed ({primary_error_msg}). Triggering DuckDuckGo fallback...")
            event_bus.publish(
                Event(
                    event_type="FallbackTriggered",
                    payload={
                        "primary": "tavily",
                        "fallback": "duckduckgo",
                        "reason": primary_error_msg,
                    },
                )
            )

            # Execute Fallback Provider (DuckDuckGo)
            try:
                ddg_response = self.fallback_provider.search(query, max_results=max_results, **kwargs)
                lat_total = round((time.time() - t0) * 1000, 2)

                if ddg_response and ddg_response.success:
                    self.fallback_success_count += 1
                    health_monitor.record_call("duckduckgo", success=True, latency_ms=lat_total)
                    event_bus.publish(
                        Event(
                            event_type="FallbackSuccess",
                            payload={
                                "primary": "tavily",
                                "fallback": "duckduckgo",
                                "latency_ms": lat_total,
                            },
                        )
                    )
                    meta = ddg_response.metadata or {}
                    meta["fallback_used"] = True
                    meta["primary_error"] = primary_error_msg
                    meta["total_latency_ms"] = lat_total
                    ddg_response.metadata = meta
                    return ddg_response
                else:
                    self.fallback_failure_count += 1
                    fb_err = ddg_response.error if ddg_response else "DuckDuckGo returned failure"
                    health_monitor.record_call("duckduckgo", success=False, latency_ms=lat_total)
                    event_bus.publish(
                        Event(
                            event_type="FallbackFailure",
                            payload={
                                "primary": "tavily",
                                "fallback": "duckduckgo",
                                "error": fb_err,
                            },
                        )
                    )
                    return ddg_response
            except Exception as fb_exc:
                lat_total = round((time.time() - t0) * 1000, 2)
                self.fallback_failure_count += 1
                health_monitor.record_call("duckduckgo", success=False, latency_ms=lat_total)
                event_bus.publish(
                    Event(
                        event_type="FallbackFailure",
                        payload={
                            "primary": "tavily",
                            "fallback": "duckduckgo",
                            "error": str(fb_exc),
                        },
                    )
                )
                return ProviderResponse(
                    success=False,
                    provider="trusted_web",
                    category=ProviderCategory.SEARCH,
                    status=ProviderStatus.ERROR.value,
                    latency_ms=lat_total,
                    error=f"Primary (Tavily) failed: {primary_error_msg}; Fallback (DuckDuckGo) failed: {str(fb_exc)}",
                )


# Global singleton instance
trusted_web_provider_manager = TrustedWebProviderManager()
