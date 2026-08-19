import pytest
import time
from unittest.mock import MagicMock, patch
from config.settings import Config
from core.llm.manager import LLMManager
from core.llm.base_provider import BaseLLMProvider, ProviderStatus, LLMResponse


class MockFailingProvider(BaseLLMProvider):
    def __init__(self, name: str, primary_model: str, delay_sec: float = 0.5):
        super().__init__(name, primary_model, primary_model, "fake-key")
        self.delay_sec = delay_sec
        self.attempt_timeouts = []

    def get_client(self, model_name: str, temperature: float = 0.1, max_tokens: int = 4096, timeout: float = 10.0):
        return None

    def generate(self, prompt_or_chain_fn, inputs, temperature=0.1, max_tokens=4096, timeout=10.0, model_override=None):
        self.attempt_timeouts.append(timeout)
        time.sleep(self.delay_sec)
        raise Exception(f"Simulated failure for {self.name} ({model_override})")


class MockSucceedingProvider(BaseLLMProvider):
    def __init__(self, name: str, primary_model: str):
        super().__init__(name, primary_model, primary_model, "fake-key")

    def get_client(self, model_name: str, temperature: float = 0.1, max_tokens: int = 4096, timeout: float = 10.0):
        return None

    def generate(self, prompt_or_chain_fn, inputs, temperature=0.1, max_tokens=4096, timeout=10.0, model_override=None):
        return f"Response from {self.name}", model_override or self.primary_model, 10, 20


def test_total_deadline_exhaustion():
    """Test 1: Manager stops attempting providers once total budget is exhausted."""
    manager = LLMManager()

    p1 = MockFailingProvider("p1", "m1", delay_sec=1.2)
    p2 = MockFailingProvider("p2", "m2", delay_sec=1.2)
    p3 = MockFailingProvider("p3", "m3", delay_sec=1.2)

    with patch.object(manager.router, "select_ordered_providers", return_value=[p1, p2, p3]):
        t0 = time.time()
        # Set small total timeout budget of 1.5s
        res = manager.generate("Test prompt", timeout=1.5)
        elapsed = time.time() - t0

        assert res.success is False
        assert elapsed < 2.5  # Should stop fast once budget is exhausted
        assert len(res.attempts_detail) < 6


def test_remaining_budget_propagation():
    """Test 2: attempt_timeout <= remaining_total_budget for every provider attempt."""
    manager = LLMManager()

    p1 = MockFailingProvider("p1", "m1", delay_sec=0.2)
    p2 = MockFailingProvider("p2", "m2", delay_sec=0.2)

    with patch.object(manager.router, "select_ordered_providers", return_value=[p1, p2]):
        manager.generate("Test prompt", timeout=3.0)

        for attempt in p1.attempt_timeouts + p2.attempt_timeouts:
            assert attempt <= 3.0


def test_fast_failure_and_fallback():
    """Test 3: Primary provider fails, fallback provider succeeds; metadata records both attempts."""
    manager = LLMManager()

    p1 = MockFailingProvider("p1", "m1", delay_sec=0.1)
    p2 = MockSucceedingProvider("p2", "m2")

    with patch.object(manager.router, "select_ordered_providers", return_value=[p1, p2]):
        res = manager.generate("Test prompt", timeout=5.0)

        assert res.success is True
        assert res.provider == "p2"
        assert res.fallback_occurred is True
        assert len(res.attempts_detail) >= 2
        assert res.attempts_detail[0]["result"] == "FAILED"
        assert res.attempts_detail[1]["result"] == "SUCCESS"


def test_invalid_unavailable_model_handling():
    """Test 4: Unavailable model fails quickly and continues to next fallback."""
    manager = LLMManager()

    class MockUnavailableProvider(BaseLLMProvider):
        def __init__(self):
            super().__init__("p1", "invalid-model", "invalid-model", "fake-key")

        def get_client(self, model_name: str, temperature: float = 0.1, max_tokens: int = 4096, timeout: float = 10.0):
            return None

        def generate(self, prompt_or_chain_fn, inputs, temperature=0.1, max_tokens=4096, timeout=10.0, model_override=None):
            raise Exception("404 NOT_FOUND: model invalid-model not found")

    p1 = MockUnavailableProvider()
    p2 = MockSucceedingProvider("p2", "m2")

    with patch.object(manager.router, "select_ordered_providers", return_value=[p1, p2]):
        res = manager.generate("Test prompt", timeout=5.0)

        assert res.success is True
        assert res.provider == "p2"


def test_oversized_request_routing():
    """Test 5: Oversized prompt (>12000 chars) for groq/compound is skipped without query corruption."""
    manager = LLMManager()

    class MockGroqProvider(BaseLLMProvider):
        def __init__(self):
            super().__init__("groq", "groq/compound", "openai/gpt-oss-20b", "fake-key")

        def get_client(self, model_name: str, temperature: float = 0.1, max_tokens: int = 4096, timeout: float = 10.0):
            return None

        def generate(self, prompt_or_chain_fn, inputs, temperature=0.1, max_tokens=4096, timeout=10.0, model_override=None):
            model = model_override or self.primary_model
            if model == "groq/compound":
                raise Exception("413 Request Entity Too Large")
            return "Groq fallback response", model, 20, 40

    p_groq = MockGroqProvider()

    oversized_prompt = "Explain quantum computing. " + ("Extra context line. " * 600)  # ~13,000 chars

    with patch.object(manager.router, "select_ordered_providers", return_value=[p_groq]):
        res = manager.generate(oversized_prompt, timeout=5.0)

        assert res.success is True
        assert res.model == "openai/gpt-oss-20b"
        # Verify groq/compound was skipped in attempts_detail
        skipped = [a for a in res.attempts_detail if a["model"] == "groq/compound" and a["result"] == "SKIPPED"]
        assert len(skipped) == 1
        assert "exceeds model payload limit" in skipped[0]["skipped_reason"]


def test_successful_primary_provider():
    """Test 6: Normal behavior remains unchanged when primary provider succeeds immediately."""
    manager = LLMManager()

    p1 = MockSucceedingProvider("p1", "m1")

    with patch.object(manager.router, "select_ordered_providers", return_value=[p1]):
        res = manager.generate("Test prompt", timeout=5.0)

        assert res.success is True
        assert res.provider == "p1"
        assert res.fallback_occurred is False
        assert len(res.attempts_detail) == 1
        assert res.attempts_detail[0]["result"] == "SUCCESS"
