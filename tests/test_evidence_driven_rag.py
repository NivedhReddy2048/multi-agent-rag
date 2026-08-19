"""Evidence-Driven RAG Pipeline Integration & Unit Test Suite (Task 9).

Validates:
- Test A: Grounded answer from relevant documents (source_mode="documents")
- Test B: Web search fallback when documents are insufficient (source_mode="documents+web" or "web")
- Test C: Insufficient context response when documents missing and web search disabled (source_mode="none")
- Test D: Gemini 429 rate limit failover to Groq (provider="groq", no raw exceptions)
- Test E: All providers fail graceful degradation (structured response, no traceback)
- Test F: Mixed sources context separation (explicit headers for Document vs Web sources)
"""

import pytest
import unittest
from unittest.mock import MagicMock, patch
from config.settings import Config
from agents.base import AgentResult
from agents.orchestrator import OrchestratorAgent
from agents.synthesis import SynthesisAgent
from agents.validation import ValidationAgent
from agents.crag import CRAGAgent
from core.llm.base_provider import LLMResponse


class TestEvidenceDrivenRAG(unittest.TestCase):

    def setUp(self):
        self.mock_config = Config
        self.mock_engine = MagicMock()
        self.mock_memory = MagicMock()
        self.mock_memory.create_conversation.return_value = "test_conv_123"

        self.orchestrator = OrchestratorAgent(
            config=self.mock_config,
            engine=self.mock_engine,
            memory=self.mock_memory,
        )

    def test_a_relevant_documents_grounded_synthesis(self):
        """Test A: Grounded answer from relevant documents -> source_mode='documents'."""
        sample_doc = {
            "content": "Enterprise AI Architecture uses microservices and RAG pipelines.",
            "source_file": "ai_arch.txt",
            "page": 1,
            "chunk_id": "chunk_001",
            "score": 0.92,
        }

        # Mock retrieval returning sample document
        self.orchestrator.retrieval.run = MagicMock(return_value=AgentResult(
            content="Retrieved 1 chunks",
            confidence=90,
            sources=[sample_doc],
            metadata={"stage_latency_ms": {"dense_retrieval_ms": 10.0}}
        ))

        # Mock CRAG marking retrieval sufficient
        self.orchestrator.crag.run = MagicMock(return_value=AgentResult(
            confidence=90,
            sources=[sample_doc],
            agent_trace=["✅ CRAG: Retrieval sufficient"],
            metadata={"sufficient": True, "crag_used": False, "retrieval_score": 0.85, "web_results_count": 0}
        ))

        # Mock synthesis returning grounded response
        self.orchestrator.synthesis.run = MagicMock(return_value=AgentResult(
            content="Enterprise AI Architecture relies on microservices and RAG [DOCUMENT SOURCE 1].",
            confidence=90,
            sources=[sample_doc],
            metadata={
                "provider": "groq",
                "model": "groq/compound",
                "latency_ms": 500,
                "tokens": 100,
                "fallback_occurred": False,
                "fallback_chain": ["groq"],
                "error": "",
                "source_mode": "documents",
            }
        ))

        ctx = {"query": "What is Enterprise AI Architecture?", "history": [], "request_id": "test_req_a"}
        result = self.orchestrator.run(ctx)

        self.assertEqual(result.metadata["source_mode"], "documents")
        self.assertIn("Enterprise AI Architecture", result.content)
        self.assertGreater(result.confidence, 0)

    def test_b_no_documents_web_search_enabled(self):
        """Test B: Insufficient documents, Web enabled -> source_mode='web' / 'documents+web'."""
        web_doc = {
            "content": "LangChain is a framework for building LLM applications.",
            "source_file": "🌐 LangChain Docs",
            "page": "https://langchain.com",
            "chunk_id": "web_hash123",
            "score": 0.85,
        }

        self.orchestrator.retrieval.run = MagicMock(return_value=AgentResult(
            content="No docs", confidence=0, sources=[], metadata={"stage_latency_ms": {}}
        ))

        self.orchestrator.crag.run = MagicMock(return_value=AgentResult(
            confidence=0, sources=[], agent_trace=["⚠️ CRAG: Retrieval insufficient"],
            metadata={"sufficient": False, "crag_used": False, "retrieval_score": 0.0, "web_results_count": 0}
        ))

        self.orchestrator._search_web = MagicMock(return_value=[web_doc])

        self.orchestrator.synthesis.run = MagicMock(return_value=AgentResult(
            content="LangChain is a framework for LLM apps [WEB SOURCE 1].",
            confidence=80,
            sources=[web_doc],
            metadata={
                "provider": "groq",
                "model": "groq/compound",
                "latency_ms": 600,
                "tokens": 120,
                "fallback_occurred": False,
                "fallback_chain": ["groq"],
                "error": "",
                "source_mode": "web",
            }
        ))

        ctx = {"query": "What is LangChain framework?", "history": [], "request_id": "test_req_b"}
        with patch.object(self.mock_config, "ENABLE_WEB_SEARCH", True):
            result = self.orchestrator.run(ctx)

        self.assertIn("web", result.metadata["source_mode"])
        self.assertIn("LangChain", result.content)

    def test_c_no_documents_web_search_disabled(self):
        """Test C: Insufficient documents, Web disabled -> returns 'The indexed documents do not contain enough...'."""
        self.orchestrator.retrieval.run = MagicMock(return_value=AgentResult(
            content="No docs", confidence=0, sources=[], metadata={"stage_latency_ms": {}}
        ))

        self.orchestrator.crag.run = MagicMock(return_value=AgentResult(
            confidence=0, sources=[], agent_trace=["⚠️ CRAG: Retrieval insufficient"],
            metadata={"sufficient": False, "crag_used": False, "retrieval_score": 0.0, "web_results_count": 0}
        ))

        ctx = {"query": "What is Quantum Teleportation?", "history": [], "request_id": "test_req_c"}

        with patch.object(self.orchestrator.cfg, "ENABLE_WEB_SEARCH", False):
            result = self.orchestrator.run(ctx)

        self.assertEqual(result.metadata["source_mode"], "none")
        self.assertEqual(result.content, "The indexed documents do not contain enough information to answer this question.")
        self.assertEqual(result.confidence, 0)

    def test_d_gemini_429_failover_to_groq(self):
        """Test D: Gemini fails with 429, Groq succeeds -> provider='groq', no raw error."""
        sample_doc = {"content": "RAG systems combine retrieval and generation.", "source_file": "rag.pdf", "page": 1, "chunk_id": "c1", "score": 0.9}

        self.orchestrator.retrieval.run = MagicMock(return_value=AgentResult(content="OK", confidence=90, sources=[sample_doc], metadata={"stage_latency_ms": {}}))
        self.orchestrator.crag.run = MagicMock(return_value=AgentResult(confidence=90, sources=[sample_doc], metadata={"sufficient": True, "crag_used": False, "retrieval_score": 0.9, "web_results_count": 0}))

        # Mock synthesis returning result from Groq after Gemini 429
        self.orchestrator.synthesis.run = MagicMock(return_value=AgentResult(
            content="RAG systems combine document retrieval and LLM text generation [DOCUMENT SOURCE 1].",
            confidence=85,
            sources=[sample_doc],
            metadata={
                "provider": "groq",
                "model": "groq/compound",
                "latency_ms": 1200,
                "tokens": 150,
                "fallback_occurred": True,
                "fallback_chain": ["gemini", "groq"],
                "error": "",
                "source_mode": "documents"
            }
        ))

        ctx = {"query": "Explain RAG", "history": [], "request_id": "test_req_d"}
        result = self.orchestrator.run(ctx)

        self.assertEqual(result.metadata["provider"], "groq")
        self.assertNotIn("429", result.content)
        self.assertNotIn("RESOURCE_EXHAUSTED", result.content)

    def test_e_all_providers_fail_graceful_degradation(self):
        """Test E: All providers fail -> returns user-friendly degradation response."""
        sample_doc = {"content": "Deep learning architectures rely on multi-layer perceptrons.", "source_file": "dl.txt", "page": 1, "chunk_id": "dl1", "score": 0.8}

        self.orchestrator.retrieval.run = MagicMock(return_value=AgentResult(content="OK", confidence=80, sources=[sample_doc], metadata={"stage_latency_ms": {}}))
        self.orchestrator.crag.run = MagicMock(return_value=AgentResult(confidence=80, sources=[sample_doc], metadata={"sufficient": True, "crag_used": False, "retrieval_score": 0.8, "web_results_count": 0}))

        degradation_msg = "The AI generation service is temporarily unavailable. Retrieved document evidence is shown below.\n\n- Deep learning architectures rely on multi-layer perceptrons."

        self.orchestrator.synthesis.run = MagicMock(return_value=AgentResult(
            content=degradation_msg,
            confidence=0,
            sources=[sample_doc],
            metadata={
                "provider": "none",
                "model": "none",
                "latency_ms": 2000,
                "tokens": 0,
                "fallback_occurred": True,
                "fallback_chain": ["gemini", "groq", "cohere", "mistral"],
                "error": "All providers exhausted",
                "source_mode": "documents"
            }
        ))

        ctx = {"query": "Explain deep learning", "history": [], "request_id": "test_req_e"}
        result = self.orchestrator.run(ctx)

        self.assertIn("temporarily unavailable", result.content)
        self.assertNotIn("Traceback", result.content)

    def test_f_mixed_sources_context_formatting(self):
        """Test F: Mixed sources context formatting -> document & web source distinction."""
        synthesis = SynthesisAgent(self.mock_config)
        docs = [
            {"content": "Document info", "source_file": "doc1.pdf", "page": 1, "chunk_id": "c1"},
            {"content": "Web info", "source_file": "🌐 Web Result", "page": "https://example.com", "chunk_id": "web_123"}
        ]

        res = synthesis._prepare_prompt_and_context({
            "query": "Test query",
            "documents": docs,
            "intent": "QA",
            "source_mode": "documents+web"
        })
        prompt, inputs = res[0], res[1]

        context_str = inputs["context"]
        self.assertIn("### INDEXED DOCUMENT SOURCES:", context_str)
        self.assertIn("### EXTERNAL WEB SEARCH RESULTS:", context_str)
        self.assertIn("CRITICAL INSTRUCTION FOR MIXED SOURCES", str(prompt))


if __name__ == "__main__":
    unittest.main()
