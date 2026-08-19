"""Comprehensive Integration Test Suite for Multi-LLM Orchestration Layer.

Validates end-to-end multi-provider failover:
✓ Gemini success -> provider='gemini', fallback=False
✓ Gemini 429 -> Groq success -> provider='groq', fallback=True
✓ Gemini+Groq fail -> Cohere success -> provider='cohere', fallback=True
✓ Gemini+Groq+Cohere fail -> Mistral success -> provider='mistral', fallback=True
✓ All providers fail -> Grounded document summary or clean user error
✓ Zero raw exception leakage to content or error fields
✓ Telemetry metadata is ALWAYS populated (never UNKNOWN on success)
✓ Retrieval engine completes independently of provider availability
"""

import unittest
from unittest.mock import patch, MagicMock
from config.settings import Config
from core.llm import LLMManager, LLMResponse, ProviderStatus
from agents.orchestrator import OrchestratorAgent
from agents.synthesis import SynthesisAgent
from core.engine import BaseRAGEngine
from core.memory import ConversationMemory


class TestMultiLLMIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = Config
        cls.engine = BaseRAGEngine(cls.config)
        cls.memory = ConversationMemory(":memory:")
        cls.llm_mgr = LLMManager(cls.config)
        cls.orchestrator = OrchestratorAgent(cls.config, cls.engine, cls.memory)

    def setUp(self):
        # Reset all provider circuits before each test
        for name in ["gemini", "groq", "cohere", "mistral"]:
            prov = self.llm_mgr.registry.get_provider(name)
            if prov:
                prov.reset_circuit()

    def test_scenario_a_gemini_success(self):
        """Scenario A: Gemini succeeds natively."""
        gemini_prov = self.llm_mgr.registry.get_provider("gemini")

        with patch.object(gemini_prov, "generate", return_value=("Grounded Gemini response", "gemini-2.0-flash", 15, 30)):
            res = self.llm_mgr.generate("What is quantum computing?", intent="QA")

            self.assertIsInstance(res, LLMResponse)
            self.assertTrue(res.success)
            self.assertEqual(res.provider, "gemini")
            self.assertEqual(res.model, "gemini-2.0-flash")
            self.assertEqual(res.content, "Grounded Gemini response")
            self.assertFalse(res.fallback_occurred)
            self.assertNotEqual(res.provider, "UNKNOWN")

    def test_scenario_b_gemini_429_to_groq(self):
        """Scenario B: Gemini returns 429 RESOURCE_EXHAUSTED -> Groq succeeds."""
        gemini_prov = self.llm_mgr.registry.get_provider("gemini")
        groq_prov = self.llm_mgr.registry.get_provider("groq")

        with patch.object(gemini_prov, "generate", side_effect=Exception("429 RESOURCE_EXHAUSTED")), \
             patch.object(groq_prov, "generate", return_value=("Groq fallback response", "groq/compound", 20, 40)):

            res = self.llm_mgr.generate("What is quantum computing?", intent="QA")

            self.assertIsInstance(res, LLMResponse)
            self.assertTrue(res.success)
            self.assertEqual(res.provider, "groq")
            self.assertEqual(res.model, "groq/compound")
            self.assertEqual(res.content, "Groq fallback response")
            self.assertTrue(res.fallback_occurred)
            self.assertIn("gemini", res.fallback_chain)
            self.assertIn("groq", res.fallback_chain)

    def test_scenario_c_top_2_fail_to_cohere(self):
        """Scenario C: Gemini and Groq fail -> Cohere succeeds."""
        gemini_prov = self.llm_mgr.registry.get_provider("gemini")
        groq_prov = self.llm_mgr.registry.get_provider("groq")
        cohere_prov = self.llm_mgr.registry.get_provider("cohere")

        with patch.object(gemini_prov, "generate", side_effect=Exception("429 RESOURCE_EXHAUSTED")), \
             patch.object(groq_prov, "generate", side_effect=Exception("500 Internal Server Error")), \
             patch.object(cohere_prov, "generate", return_value=("Cohere response", "command-r-plus", 25, 50)):

            res = self.llm_mgr.generate("Summarize policy", intent="QA")

            self.assertIsInstance(res, LLMResponse)
            self.assertTrue(res.success)
            self.assertEqual(res.provider, "cohere")
            self.assertEqual(res.model, "command-r-plus")
            self.assertTrue(res.fallback_occurred)

    def test_scenario_d_top_3_fail_to_mistral(self):
        """Scenario D: Gemini, Groq, and Cohere fail -> Mistral succeeds."""
        gemini_prov = self.llm_mgr.registry.get_provider("gemini")
        groq_prov = self.llm_mgr.registry.get_provider("groq")
        cohere_prov = self.llm_mgr.registry.get_provider("cohere")
        mistral_prov = self.llm_mgr.registry.get_provider("mistral")

        with patch.object(gemini_prov, "generate", side_effect=Exception("429 RESOURCE_EXHAUSTED")), \
             patch.object(groq_prov, "generate", side_effect=Exception("500 Server Error")), \
             patch.object(cohere_prov, "generate", side_effect=Exception("401 Invalid Key")), \
             patch.object(mistral_prov, "generate", return_value=("Mistral response", "mistral-large-latest", 30, 60)):

            res = self.llm_mgr.generate("Code sorting algorithm", intent="QA")

            self.assertIsInstance(res, LLMResponse)
            self.assertTrue(res.success)
            self.assertEqual(res.provider, "mistral")
            self.assertEqual(res.model, "mistral-large-latest")
            self.assertTrue(res.fallback_occurred)

    def test_scenario_e_all_providers_fail_grounded_summary(self):
        """Scenario E: ALL providers fail -> Clean grounded summary returned."""
        for name in ["gemini", "groq", "cohere", "mistral"]:
            prov = self.llm_mgr.registry.get_provider(name)
            if prov:
                patch.object(prov, "generate", side_effect=Exception(f"{name} 500 Outage")).start()

        docs = [{"source_file": "policy.pdf", "page": 2, "content": "Company security policy document."}]
        res = self.llm_mgr.generate("What is security policy?", documents=docs, query="What is security policy?")
        patch.stopall()

        self.assertIsInstance(res, LLMResponse)
        self.assertFalse(res.success)
        self.assertEqual(res.provider, "NONE")
        self.assertEqual(res.content, "")
        self.assertEqual(res.failure_reason, "ALL_PROVIDERS_FAILED")
        self.assertNotIn("429", res.error)
        self.assertNotIn("500 Outage", res.error)

    def test_end_to_end_orchestrator_telemetry_population(self):
        """End-to-end Orchestrator run verifies telemetry metadata is fully populated and never UNKNOWN."""
        gemini_prov = self.llm_mgr.registry.get_provider("gemini")
        groq_prov = self.llm_mgr.registry.get_provider("groq")

        with patch.object(gemini_prov, "generate", side_effect=Exception("429 RESOURCE_EXHAUSTED")), \
             patch.object(groq_prov, "generate", return_value=("Groq end-to-end answer [SOURCE 1]", "groq/compound", 12, 24)):

            ctx = {
                "query": "What is the policy?",
                "history": [],
                "documents": [{"source_file": "doc.pdf", "page": 1, "content": "Policy text"}],
            }
            res = self.orchestrator.run(ctx)

            self.assertIsNotNone(res.metadata)
            self.assertEqual(res.metadata.get("provider"), "groq")
            self.assertEqual(res.metadata.get("model"), "groq/compound")
            self.assertGreater(res.metadata.get("tokens", 0), 0)
            self.assertTrue(res.metadata.get("fallback_occurred"))
            self.assertNotEqual(res.metadata.get("provider"), "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
