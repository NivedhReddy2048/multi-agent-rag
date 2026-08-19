"""EKIP Phase 3.0 Provider Resilience, Circuit Breaker & Telemetry Accuracy Test Suite."""

import pytest
import time
from typing import Dict, Any, Optional
from unittest.mock import MagicMock, patch

from core.llm.base_provider import BaseLLMProvider, ProviderStatus, LLMResponse
from core.llm.manager import LLMManager
from config import Config


class MockFailingProvider(BaseLLMProvider):
    """Mock provider configurable to simulate timeouts, rate limits, 404s, or internal errors."""
    def __init__(self, name: str, fail_type: str = None, success_text: str = "Mocked LLM Response"):
        super().__init__(name, f"{name}-primary", f"{name}-fallback", f"api_key_{name}")
        self.fail_type = fail_type
        self.success_text = success_text
        self.call_count = 0

    def get_client(self, model_name: str, temperature: float = 0.1, max_tokens: int = 4096, timeout: float = 2.0):
        return None

    def generate(self, prompt_or_chain_fn, inputs: Dict[str, Any], temperature: float = 0.1, max_tokens: int = 4096, timeout: float = 2.0, model_override: str = None):
        self.call_count += 1
        if self.fail_type == "timeout":
            raise Exception("ReadTimeout: The read operation timed out")
        elif self.fail_type == "429":
            raise Exception("HTTP 429: Rate limit exceeded (RESOURCE_EXHAUSTED)")
        elif self.fail_type == "404":
            raise Exception("HTTP 404: Model 'gemini-1.5-flash' not found")
        elif self.fail_type == "type_error":
            raise TypeError("Internal programming type mismatch error")
        elif self.fail_type == "attribute_error":
            raise AttributeError("Internal attribute missing")
        elif self.fail_type == "key_error":
            raise KeyError("Missing key in dict")
        elif self.fail_type == "value_error":
            raise ValueError("Invalid value passed")
        elif self.fail_type == "malformed":
            return ("", model_override or self.primary_model, 0, 0)
        
        return (f"{self.success_text} from {self.name}", model_override or self.primary_model, 10, 20)


@pytest.fixture
def clean_llm_manager():
    """Reset LLMManager singleton before each test."""
    LLMManager._instance = None
    mgr = LLMManager(Config)
    return mgr


# ============================================================
# OBJECTIVE 2 — PROVIDER FAILURE SCENARIOS
# ============================================================

def test_case_a_primary_timeout_fallback_succeeds(clean_llm_manager):
    """Case A: Primary provider timeouts -> fallback provider succeeds."""
    p1 = MockFailingProvider("p1_timeout", fail_type="timeout")
    p2 = MockFailingProvider("p2_success", fail_type=None)
    clean_llm_manager.registry.providers = {"p1_timeout": p1, "p2_success": p2}

    resp = clean_llm_manager.generate("Test prompt")
    assert resp.success is True
    assert resp.provider == "p2_success"
    assert resp.fallback_occurred is True
    assert "p1_timeout" in resp.fallback_chain
    assert "p2_success" in resp.fallback_chain


def test_case_b_primary_rate_limit_fallback_succeeds(clean_llm_manager):
    """Case B: Primary provider returns 429 rate limit -> fallback provider succeeds."""
    p1 = MockFailingProvider("p1_429", fail_type="429")
    p2 = MockFailingProvider("p2_success", fail_type=None)
    clean_llm_manager.registry.providers = {"p1_429": p1, "p2_success": p2}

    resp = clean_llm_manager.generate("Test prompt")
    assert resp.success is True
    assert resp.provider == "p2_success"
    assert resp.fallback_occurred is True
    assert p1.current_status == ProviderStatus.RATE_LIMITED


def test_case_c_primary_404_unavailable_fallback_succeeds(clean_llm_manager):
    """Case C: Primary provider returns 404 model unavailable -> fallback succeeds."""
    p1 = MockFailingProvider("p1_404", fail_type="404")
    p2 = MockFailingProvider("p2_success", fail_type=None)
    clean_llm_manager.registry.providers = {"p1_404": p1, "p2_success": p2}

    resp = clean_llm_manager.generate("Test prompt")
    assert resp.success is True
    assert resp.provider == "p2_success"
    assert resp.fallback_occurred is True


def test_case_e_all_providers_fail(clean_llm_manager):
    """Case F: All providers fail -> returns controlled failure without crashing."""
    p1 = MockFailingProvider("p1_timeout", fail_type="timeout")
    p2 = MockFailingProvider("p2_429", fail_type="429")
    clean_llm_manager.registry.providers = {"p1_timeout": p1, "p2_429": p2}

    resp = clean_llm_manager.generate("Test prompt")
    assert resp.success is False
    assert resp.provider == "NONE"
    assert resp.error == "ALL_PROVIDERS_FAILED"
    assert resp.fallback_occurred is False


# ============================================================
# OBJECTIVE 3 — DISTINGUISH FAILURE TYPES
# ============================================================

@pytest.mark.parametrize("error_type, exc_class", [
    ("type_error", TypeError),
    ("attribute_error", AttributeError),
    ("key_error", KeyError),
    ("value_error", ValueError),
])
def test_programming_errors_do_not_trigger_fallback(clean_llm_manager, error_type, exc_class):
    """Objective 3: Internal programming errors must NOT trigger provider fallback."""
    p1 = MockFailingProvider("p1_buggy", fail_type=error_type)
    p2 = MockFailingProvider("p2_success", fail_type=None)
    clean_llm_manager.registry.providers = {"p1_buggy": p1, "p2_success": p2}

    with pytest.raises(exc_class):
        clean_llm_manager.generate("Test prompt")


# ============================================================
# OBJECTIVE 4 — CIRCUIT BREAKER VERIFICATION
# ============================================================

def test_circuit_breaker_tripping_and_isolation():
    """Objective 4: Verify circuit trips to OPEN and isolates failing provider."""
    p = MockFailingProvider("test_cb", fail_type="429")
    assert p.is_circuit_open() is False

    p.trip_circuit(ProviderStatus.RATE_LIMITED, cooldown_seconds=60.0)
    assert p.is_circuit_open() is True

    # Call reset
    p.reset_circuit()
    assert p.is_circuit_open() is False


# ============================================================
# OBJECTIVE 6 — TELEMETRY ACCURACY
# ============================================================

def test_telemetry_accuracy_all_providers_failed(clean_llm_manager):
    """Objective 6: Verify telemetry accuracy when all providers fail."""
    p1 = MockFailingProvider("p1_timeout", fail_type="timeout")
    clean_llm_manager.registry.providers = {"p1_timeout": p1}

    resp = clean_llm_manager.generate("Test prompt")
    assert resp.success is False
    assert resp.fallback_occurred is False
    assert resp.tokens == 0
    assert resp.provider == "NONE"


def test_telemetry_accuracy_successful_fallback(clean_llm_manager):
    """Objective 6: Verify telemetry accuracy when fallback succeeds."""
    p1 = MockFailingProvider("p1_timeout", fail_type="timeout")
    p2 = MockFailingProvider("p2_ok", fail_type=None)
    clean_llm_manager.registry.providers = {"p1_timeout": p1, "p2_ok": p2}

    resp = clean_llm_manager.generate("Test prompt")
    assert resp.success is True
    assert resp.fallback_occurred is True
    assert resp.provider == "p2_ok"
    assert resp.tokens == 30  # 10 prompt + 20 completion tokens
