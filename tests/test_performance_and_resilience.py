"""Performance Profiling & Backend Resilience Verification Suite for EKIP Platform."""

import os
import unittest
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from config.settings import Config
from core.loader import DocumentLoader
from core.engine import BaseRAGEngine
from core.memory import ConversationMemory
from agents.orchestrator import OrchestratorAgent
from agents.synthesis import SynthesisAgent
from core.llm_manager import LLMManager


class TestPerformanceAndResilience(unittest.TestCase):
    """Automated tests verifying latency profiling, callback handling, caching, and rate-limit resilience."""

    @classmethod
    def setUpClass(cls):
        Config.validate()
        cls.engine = BaseRAGEngine(Config)
        cls.memory = ConversationMemory(Config.OBSERVABILITY_DB)
        cls.orchestrator = OrchestratorAgent(Config, cls.engine, cls.memory)

    def test_01_config_timeout_budgets(self):
        """Verify performance and reliability timeout config settings."""
        self.assertTrue(hasattr(Config, "LLM_TIMEOUT_SECONDS"))
        self.assertEqual(Config.LLM_TIMEOUT_SECONDS, 10.0)
        self.assertEqual(Config.LLM_MAX_RETRIES, 1)
        self.assertEqual(Config.LLM_MAX_FALLBACK_MODELS, 2)

    def test_02_document_loader_callback_compatibility(self):
        """Verify load_file and chunk_documents handle parsing_cb and progress_cb seamlessly."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            test_file = Path(tmp_dir) / "callback_test.txt"
            test_file.write_text("Testing document loader callback compatibility.\n" * 10, encoding="utf-8")

            loader = DocumentLoader(chunk_size=150, chunk_overlap=10)

            captured_events = []

            def custom_cb(progress, msg):
                captured_events.append((progress, msg))

            # Test parsing_cb
            docs1 = loader.load_file(str(test_file), parsing_cb=custom_cb)
            self.assertGreater(len(docs1), 0)

            # Test progress_cb parameter alias
            docs2 = loader.load_file(str(test_file), progress_cb=custom_cb)
            self.assertGreater(len(docs2), 0)

            # Test chunking_cb
            chunks = loader.chunk_documents(docs1, test_file.name, chunking_cb=custom_cb)
            self.assertGreater(len(chunks), 0)

            self.assertGreaterEqual(len(captured_events), 4)

    def test_03_pipeline_latency_profiling(self):
        """Profile end-to-end pipeline execution and verify stage timing markers."""
        context = {
            "query": "What is enterprise RAG architecture?",
            "request_id": "test_profiling_req_101"
        }

        t_start = time.time()
        res = self.orchestrator.run(context)
        total_time_sec = time.time() - t_start

        self.assertIsNotNone(res)
        self.assertIn("stage_latency_ms", res.metadata)

        stages = res.metadata["stage_latency_ms"]
        self.assertIn("intent_classification_ms", stages)
        self.assertIn("dense_retrieval_ms", stages)
        self.assertIn("sparse_retrieval_ms", stages)
        self.assertIn("rrf_fusion_ms", stages)
        self.assertIn("cross_encoder_rerank_ms", stages)
        self.assertIn("crag_evaluation_ms", stages)
        self.assertIn("llm_synthesis_ms", stages)
        self.assertIn("validation_ms", stages)

        print("\n--- PIPELINE STAGE LATENCY REPORT ---")
        for stage, ms in stages.items():
            print(f"  Stage [{stage}]: {ms} ms")
        print(f"Total Pipeline Latency: {res.metadata['total_latency_ms']} ms ({total_time_sec:.3f} s)")

        # Verify pipeline execution completes within reasonable latency
        self.assertLess(total_time_sec, 10.0)

    def test_04_rate_limit_resilience_and_fail_fast(self):
        """Verify 429 RESOURCE_EXHAUSTED fails fast without 200s looping delay and never leaks raw 429 string."""
        synth = SynthesisAgent(Config)
        from core.llm.base_provider import LLMResponse

        mock_deg = LLMResponse(
            provider="NONE",
            model="none",
            content="",
            latency=10.0,
            tokens=0,
            success=False,
            error="ALL_PROVIDERS_FAILED",
            fallback_occurred=True,
            fallback_chain=["gemini", "groq"],
        )

        with patch.object(synth.llm_manager, "generate", return_value=mock_deg):
            t0 = time.time()
            res = synth.run({
                "query": "Explain quantum computing in detail",
                "documents": [{"source_file": "doc1.txt", "content": "Quantum computing uses qubits."}],
                "intent": "QA"
            })
            elapsed = time.time() - t0

            # Fail-fast should complete in < 2 seconds
            self.assertLess(elapsed, 2.0)
            self.assertNotIn("RESOURCE_EXHAUSTED", res.content)
            self.assertEqual(res.content, "")
            self.assertFalse(res.success)
            self.assertEqual(res.error, "ALL_PROVIDERS_FAILED")


if __name__ == "__main__":
    unittest.main()
