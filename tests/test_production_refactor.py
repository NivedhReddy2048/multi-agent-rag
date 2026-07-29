"""Regression tests for the production-readiness evidence-decision refactor."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from agents.base import AgentResult
from agents.crag import CRAGAgent
from agents.orchestrator import OrchestratorAgent
from agents.validation import ValidationAgent
from analytics.telemetry import TelemetryTracker
from config.settings import Config
from core.memory import ConversationMemory
from core.llm import LLMManager


class TestProductionRefactor(unittest.TestCase):
    def setUp(self):
        self.engine = MagicMock()
        self.memory = MagicMock()
        self.orchestrator = OrchestratorAgent(Config, self.engine, self.memory)
        self.doc = {
            "content": "The retention policy requires records to be retained for seven years.",
            "source_file": "policy.txt", "page": 1, "chunk_id": "doc_1", "score": 0.9,
        }
        self.web = {
            "content": "External regulations describe seven-year record retention.",
            "snippet": "External regulations describe seven-year record retention.",
            "title": "External regulations", "url": "https://example.test/retention",
            "domain": "example.test", "source_file": "🌐 External regulations",
            "page": "https://example.test/retention", "chunk_id": "web_1", "score": 0.85,
        }

    def _stub_retrieval_and_crag(self, docs, sufficient, score=0.8):
        self.orchestrator.retrieval.run = MagicMock(return_value=AgentResult(
            sources=docs, confidence=80, metadata={"stage_latency_ms": {}}
        ))
        self.orchestrator.crag.run = MagicMock(return_value=AgentResult(
            confidence=int(score * 100), metadata={"sufficient": sufficient, "retrieval_score": score}
        ))

    def test_crag_only_evaluates_and_has_no_web_search_method(self):
        self.assertFalse(hasattr(CRAGAgent(Config), "web_search"))
        result = CRAGAgent(Config).run({"query": "unseen topic", "documents": []})
        self.assertFalse(result.metadata["sufficient"])
        self.assertEqual(result.sources, [])

    def test_documents_only_source_mode_and_confidence_independence(self):
        self._stub_retrieval_and_crag([self.doc], True)
        self.orchestrator.synthesis.run = MagicMock(return_value=AgentResult(
            content="Records must be retained for seven years [DOCUMENT SOURCE 1].",
            metadata={"provider": "gemini", "model": "test", "success": True},
        ))
        result = self.orchestrator.run({"query": "What retention?", "history": []})
        self.assertEqual(result.metadata["source_mode"], "documents")
        self.assertNotEqual(result.confidence, int(result.metadata["faithfulness"] * 100))

    def test_web_only_and_no_evidence_modes(self):
        self._stub_retrieval_and_crag([], False, 0.0)
        self.orchestrator._search_web = MagicMock(return_value=[self.web])
        self.orchestrator.synthesis.run = MagicMock(return_value=AgentResult(
            content="External regulations describe retention [WEB SOURCE 1].",
            metadata={"provider": "groq", "model": "test", "success": True},
        ))
        web_result = self.orchestrator.run({"query": "What external rule?", "history": []})
        self.assertEqual(web_result.metadata["source_mode"], "web")

        self._stub_retrieval_and_crag([], False, 0.0)
        self.orchestrator.cfg.ENABLE_WEB_SEARCH = False
        none_result = self.orchestrator.run({"query": "What missing rule?", "history": []})
        self.assertEqual(none_result.metadata["source_mode"], "none")
        self.orchestrator.cfg.ENABLE_WEB_SEARCH = True

    def test_mixed_evidence_sections_are_structurally_enforced(self):
        self._stub_retrieval_and_crag([self.doc], False, 0.2)
        self.orchestrator._search_web = MagicMock(return_value=[self.web])
        self.orchestrator.synthesis.run = MagicMock(return_value=AgentResult(
            content="Merged response [DOCUMENT SOURCE 1] [WEB SOURCE 1].",
            metadata={"provider": "gemini", "model": "test", "success": True},
        ))
        result = self.orchestrator.run({"query": "Compare retention", "history": []})
        self.assertEqual(result.metadata["source_mode"], "documents+web")
        self.assertIn("Information from Indexed Documents", result.content)
        self.assertIn("Information from External Web Sources", result.content)
        self.assertNotIn("MIXED_EVIDENCE_SECTIONS_MISSING", result.metadata["validation_warnings"])

    def test_validation_preserves_valid_content_and_source_mode(self):
        answer = "Records are retained for seven years [DOCUMENT SOURCE 1]."
        result = ValidationAgent().run({"answer": answer, "sources": [self.doc], "source_mode": "documents"})
        self.assertEqual(result.content, answer)
        self.assertEqual(result.metadata["source_mode"], "documents")
        self.assertEqual(result.confidence, 0)

    def test_gemini_429_fails_over_to_groq_without_user_error_content(self):
        manager = LLMManager(Config)
        gemini = manager.registry.get_provider("gemini")
        groq = manager.registry.get_provider("groq")
        gemini.reset_circuit()
        groq.reset_circuit()
        with patch.object(gemini, "generate", side_effect=Exception("429 RESOURCE_EXHAUSTED")), \
             patch.object(groq, "generate", return_value=("Grounded answer", "groq-test", 3, 4)):
            result = manager.generate("controlled failover", timeout=0.01)
        self.assertTrue(result.success)
        self.assertEqual(result.provider, "groq")
        self.assertNotIn("429", result.content)
        self.assertTrue(gemini.is_circuit_open())

    def test_all_provider_failures_are_structured_not_user_fallback_content(self):
        manager = LLMManager(Config)
        providers = [manager.registry.get_provider(name) for name in ("gemini", "groq", "cohere", "mistral")]
        for provider in providers:
            provider.reset_circuit()
        patches = [patch.object(provider, "generate", side_effect=Exception("500 unavailable")) for provider in providers]
        for provider_patch in patches:
            provider_patch.start()
        try:
            result = manager.generate("controlled all-fail", documents=[self.doc], query="controlled all-fail", timeout=0.01)
        finally:
            for provider_patch in patches:
                provider_patch.stop()
        self.assertFalse(result.success)
        self.assertEqual(result.content, "")
        self.assertEqual(result.failure_reason, "ALL_PROVIDERS_FAILED")

    def test_conversation_and_telemetry_persist_source_mode(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            memory = ConversationMemory(str(Path(temp_dir) / "memory.sqlite"))
            conversation_id = memory.create_conversation()
            memory.add_message(conversation_id, "assistant", "Web answer", metadata={"source_mode": "web"})
            self.assertEqual(memory.get_messages(conversation_id)[0]["metadata"]["source_mode"], "web")
            TelemetryTracker.record_query_metrics(
                memory_instance=memory, query="web query", intent="QA", confidence=50,
                faithfulness=0.5, blocked=False, latency_ms=10, agent_trace=[], source_mode="web",
            )
            self.assertEqual(memory.get_all_analytics()[0]["source_mode"], "web")


if __name__ == "__main__":
    unittest.main()
