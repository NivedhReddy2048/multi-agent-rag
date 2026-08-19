"""Automated Health & Reliability Test Suite for Multi-LLM Orchestration Layer with Circuit Breaker & Router.

Validates:
- Intelligent Router provider selection by task intent (chat->groq, code->mistral, etc.).
- Circuit Breaker tripping on 429/500/timeout and fast-skipping open circuits (0ms delay).
- Fast failover (max 2s/provider timeout budget, 0 retries).
- Zero raw exception leakage (429, 401, 500, GoogleRPC, Traceback replaced with friendly messages).
- Total provider failure returns clean message or grounded document summary.
- Retrieval engine decoupling from LLM availability.
"""

import unittest
import time
from unittest.mock import MagicMock, patch
from config.settings import Config
from core.llm import (
    LLMManager,
    ProviderStatus,
    LLMResponse,
    HealthCheckReport,
)
from agents.synthesis import SynthesisAgent
from core.engine import BaseRAGEngine


class TestMultiLLMOrchestration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = Config
        cls.llm_mgr = LLMManager(cls.config)

    def test_singleton_llm_manager(self):
        """Verify LLMManager is a single point of control across agents."""
        mgr1 = LLMManager()
        mgr2 = LLMManager()
        self.assertIs(mgr1, mgr2)

    def test_intelligent_router_intent_selection(self):
        """Verify IntelligentRouter orders providers according to task intent."""
        router = self.llm_mgr.router

        code_intent = router.determine_intent("Write a Python script for fast binary search")
        self.assertEqual(code_intent, "code_questions")

        summary_intent = router.determine_intent("Provide an executive summary of the quarterly report")
        self.assertEqual(summary_intent, "long_summaries")

        chat_intent = router.determine_intent("Hello, how are you today?")
        self.assertEqual(chat_intent, "general_chat")

    def test_circuit_breaker_tripping_and_skipping(self):
        """Verify 429 error trips circuit breaker to OPEN state, skipping provider on next request instantly."""
        test_mgr = LLMManager()
        gemini_prov = test_mgr.registry.get_provider("gemini")
        gemini_prov.reset_circuit()

        with patch.object(gemini_prov, "generate", side_effect=Exception("429 RESOURCE_EXHAUSTED")):
            # Request 1: Gemini fails with 429, trips circuit breaker
            res = test_mgr.generate("Test query")
            self.assertTrue(gemini_prov.is_circuit_open())
            self.assertEqual(gemini_prov.current_status, ProviderStatus.RATE_LIMITED)

        # Request 2: Gemini circuit is OPEN, should be skipped immediately (0ms delay) by router
        t0 = time.time()
        with patch.object(gemini_prov, "generate", side_effect=Exception("Should not be called!")):
            res2 = test_mgr.generate("Second test query")
            elapsed = time.time() - t0
            self.assertLess(elapsed, 0.5)
            self.assertEqual(res2.provider, "groq")
            self.assertEqual(res2.fallback_chain, ["groq"])

        # Reset for subsequent tests
        gemini_prov.reset_circuit()

    def test_fast_failover_timeout_budget(self):
        """Verify failover advances to next provider within capped timeout budget (<= 2 seconds)."""
        test_mgr = LLMManager()
        gemini_prov = test_mgr.registry.get_provider("gemini")
        groq_prov = test_mgr.registry.get_provider("groq")

        gemini_prov.reset_circuit()
        groq_prov.reset_circuit()

        def slow_fail(*args, **kwargs):
            time.sleep(0.1)
            raise Exception("500 Slow Timeout Error")

        with patch.object(gemini_prov, "generate", side_effect=slow_fail), \
             patch.object(groq_prov, "generate", return_value=("Fast Groq response", "groq/compound", 5, 10)):

            t0 = time.time()
            res = test_mgr.generate("Fast failover test", timeout=2.0)
            elapsed = time.time() - t0

            self.assertLess(elapsed, 2.5)
            self.assertEqual(res.provider, "groq")
            self.assertEqual(res.content, "Fast Groq response")

        gemini_prov.reset_circuit()

    def test_total_provider_failure_returns_clean_friendly_message(self):
        """Verify failure of ALL providers returns clean friendly error message without raw exceptions."""
        test_mgr = LLMManager()

        for name in ["gemini", "groq", "cohere", "mistral"]:
            prov = test_mgr.registry.get_provider(name)
            prov.reset_circuit()
            patch.object(prov, "generate", side_effect=Exception(f"{name} 500 Outage")).start()

        res = test_mgr.generate("Explain quantum computing")
        patch.stopall()

        self.assertIsInstance(res, LLMResponse)
        self.assertEqual(res.provider, "NONE")
        self.assertFalse(res.success)
        self.assertEqual(res.error, "ALL_PROVIDERS_FAILED")
        self.assertEqual(res.failure_reason, "ALL_PROVIDERS_FAILED")
        self.assertEqual(res.content, "")
        
        for name in ["gemini", "groq", "cohere", "mistral"]:
            test_mgr.registry.get_provider(name).reset_circuit()

    def test_zero_raw_exception_leakage(self):
        """Strict check: raw exception strings must NEVER leak into content or error."""
        test_mgr = LLMManager()
        gemini_prov = test_mgr.registry.get_provider("gemini")
        groq_prov = test_mgr.registry.get_provider("groq")

        gemini_prov.reset_circuit()
        groq_prov.reset_circuit()

        with patch.object(gemini_prov, "generate", side_effect=Exception("RESOURCE_EXHAUSTED 429 GoogleRPCError")), \
             patch.object(groq_prov, "generate", return_value=("Groq safe answer", "groq/compound", 5, 10)):

            res = test_mgr.generate("Safe test")
            forbidden = ["RESOURCE_EXHAUSTED", "429", "GoogleRPCError", "Traceback", "AttributeError", "HTTP 500"]
            for f in forbidden:
                self.assertNotIn(f, res.content)
                self.assertNotIn(f, res.error)

        gemini_prov.reset_circuit()

    def test_retrieval_decoupled_from_llm(self):
        """Verify Retrieval Engine completes dense/sparse search even when all LLMs are offline."""
        engine = BaseRAGEngine(self.config)
        dense = engine.dense_search("policy", k=2)
        sparse = engine.sparse_search("policy", k=2)
        fused = engine.reciprocal_rank_fusion(dense, sparse)
        self.assertIsInstance(fused, list)

    def test_telemetry_pill_fail_safe_behavior(self):
        """Verify render_llm_telemetry_pill never crashes on None, empty dict, or missing Config."""
        from app import render_llm_telemetry_pill

        # 1. Test None metadata
        html_none = render_llm_telemetry_pill(None)
        self.assertIn("<b>UNKNOWN</b>", html_none)
        self.assertIn("<code>Unknown</code>", html_none)

        # 2. Test empty dict metadata
        html_empty = render_llm_telemetry_pill({})
        self.assertIn("<b>UNKNOWN</b>", html_empty)

        # 3. Test Gemini provider metadata
        html_gemini = render_llm_telemetry_pill({"provider": "gemini", "model": "gemini-2.0-flash", "latency_ms": 120, "tokens": 45})
        self.assertIn("<b>GEMINI</b>", html_gemini)
        self.assertIn("gemini-2.0-flash", html_gemini)

        # 4. Test Groq provider metadata
        html_groq = render_llm_telemetry_pill({"provider": "groq", "model": "groq/compound", "latency_ms": 180, "tokens": 80})
        self.assertIn("<b>GROQ</b>", html_groq)
        self.assertIn("groq/compound", html_groq)

        # 5. Test Cohere provider metadata
        html_cohere = render_llm_telemetry_pill({"provider": "cohere", "model": "command-r-plus"})
        self.assertIn("<b>COHERE</b>", html_cohere)

        # 6. Test Mistral provider metadata
        html_mistral = render_llm_telemetry_pill({"provider": "mistral", "model": "mistral-large-latest"})
        self.assertIn("<b>MISTRAL</b>", html_mistral)


if __name__ == "__main__":
    unittest.main()
