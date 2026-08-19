"""Unit tests for Observability Data Layer (Task 16)."""

import pytest
from core.observability import (
    check_provider_health,
    get_all_provider_health,
    get_recent_telemetry,
    get_provider_uptime_stats,
    get_token_usage_stats,
    get_failover_events,
    get_system_diagnostics,
)


def test_provider_health():
    h = check_provider_health("Groq")
    assert h["provider"] == "Groq"
    assert h["status"] in ("operational", "degraded", "down")
    assert h["latency_ms"] > 0

    all_h = get_all_provider_health()
    assert len(all_h) == 4


def test_telemetry_and_uptime():
    logs = get_recent_telemetry()
    assert len(logs) > 0
    assert "provider" in logs[0]

    uptime = get_provider_uptime_stats()
    assert "Groq" in uptime
    assert uptime["Groq"]["uptime"] > 90.0


def test_token_and_failover_stats():
    tokens = get_token_usage_stats(7)
    assert len(tokens) == 7

    failovers = get_failover_events()
    assert len(failovers) > 0


def test_system_diagnostics():
    diag = get_system_diagnostics()
    assert "vector_store" in diag
    assert "memory" in diag
    assert diag["memory"]["used_mb"] > 0
