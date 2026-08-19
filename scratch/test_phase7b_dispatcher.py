"""Unit tests for EKIP Phase 7B Dynamic Multi-Source Dispatcher."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))
import unittest
from unittest.mock import MagicMock, patch

from core.models.domain import KnowledgeResult, SourceType
from core.planner.execution_plan import ExecutionPlan
from core.planner.enums import SourceStrategy
from agents.orchestrator import OrchestratorAgent


class TestPhase7BDispatcher(unittest.TestCase):

    def setUp(self):
        self.mock_cfg = MagicMock()
        self.mock_cfg.ENABLE_WEB_SEARCH = True
        self.mock_cfg.TAVILY_API_KEY = "test_key"
        self.mock_engine = MagicMock()
        self.mock_engine.list_docs.return_value = {}
        self.mock_memory = MagicMock()

        self.orchestrator = OrchestratorAgent(self.mock_cfg, self.mock_engine, self.mock_memory)

    @patch("core.orchestrator.knowledge_orchestrator.knowledge_orchestrator.collect")
    def test_a_wikipedia_dispatch(self, mock_collect):
        """Test A: ExecutionPlan selects Wikipedia -> Wikipedia dispatcher invoked."""
        mock_coll = MagicMock()
        mock_coll.results = [
            KnowledgeResult(
                provider="wikipedia",
                source_type=SourceType.WIKIPEDIA,
                title="Transformer (deep learning)",
                content="A Transformer is a deep learning architecture...",
                url="https://en.wikipedia.org/wiki/Transformer_(deep_learning)",
                confidence=0.85,
            )
        ]
        mock_collect.return_value = mock_coll

        plan = ExecutionPlan(
            query="Tell me about Transformers",
            source_strategy=SourceStrategy.HYBRID,
            selected_sources=[SourceType.WIKIPEDIA],
        )

        res = self.orchestrator.dispatch_selected_sources(
            query="Tell me about Transformers",
            exec_plan=plan,
            context={},
        )

        self.assertIn("external_sources", res)
        ext = res["external_sources"]
        self.assertEqual(len(ext), 1)
        self.assertEqual(ext[0]["provider"], "wikipedia")
        self.assertEqual(ext[0]["source_type"], "wikipedia")
        self.assertEqual(ext[0]["url"], "https://en.wikipedia.org/wiki/Transformer_(deep_learning)")

    @patch("core.orchestrator.knowledge_orchestrator.knowledge_orchestrator.collect")
    def test_b_youtube_dispatch(self, mock_collect):
        """Test B: ExecutionPlan selects YouTube -> YouTube dispatcher invoked & video_url preserved."""
        mock_coll = MagicMock()
        mock_coll.results = [
            KnowledgeResult(
                provider="youtube",
                source_type=SourceType.VIDEO,
                title="Video: Transformers Explained",
                content="Detailed video tutorial explaining Transformers.",
                url="https://www.youtube.com/watch?v=xyz123",
                metadata={"channel": "StatQuest", "video_url": "https://www.youtube.com/watch?v=xyz123"},
                confidence=0.85,
            )
        ]
        mock_collect.return_value = mock_coll

        plan = ExecutionPlan(
            query="Transformers video tutorial",
            source_strategy=SourceStrategy.HYBRID,
            selected_sources=[SourceType.VIDEO],
        )

        res = self.orchestrator.dispatch_selected_sources(
            query="Transformers video tutorial",
            exec_plan=plan,
            context={},
        )

        ext = res["external_sources"]
        self.assertEqual(len(ext), 1)
        self.assertEqual(ext[0]["provider"], "youtube")
        self.assertEqual(ext[0]["source_type"], "video")
        self.assertEqual(ext[0]["url"], "https://www.youtube.com/watch?v=xyz123")
        self.assertEqual(ext[0]["video_url"], "https://www.youtube.com/watch?v=xyz123")

    @patch("core.orchestrator.knowledge_orchestrator.knowledge_orchestrator.collect")
    def test_c_arxiv_and_semantic_scholar_dispatch(self, mock_collect):
        """Test C: ExecutionPlan selects arXiv + Semantic Scholar -> Both dispatched."""
        mock_coll = MagicMock()
        mock_coll.results = [
            KnowledgeResult(
                provider="arxiv",
                source_type=SourceType.ARXIV,
                title="arXiv: Attention Is All You Need",
                content="Abstract of Transformer paper...",
                url="https://arxiv.org/pdf/1706.03762.pdf",
                confidence=0.90,
            ),
            KnowledgeResult(
                provider="semantic_scholar",
                source_type=SourceType.SEMANTIC_SCHOLAR,
                title="BERT: Pre-training of Deep Bidirectional Transformers",
                content="Abstract of BERT paper...",
                url="https://www.semanticscholar.org/paper/123456",
                confidence=0.90,
            ),
        ]
        mock_collect.return_value = mock_coll

        plan = ExecutionPlan(
            query="RAG research papers",
            source_strategy=SourceStrategy.RESEARCH,
            selected_sources=[SourceType.ARXIV, SourceType.SEMANTIC_SCHOLAR],
        )

        res = self.orchestrator.dispatch_selected_sources(
            query="RAG research papers",
            exec_plan=plan,
            context={},
        )

        ext = res["external_sources"]
        self.assertEqual(len(ext), 2)
        provs = [x["provider"] for x in ext]
        self.assertIn("arxiv", provs)
        self.assertIn("semantic_scholar", provs)

    @patch("core.orchestrator.knowledge_orchestrator.knowledge_orchestrator.collect")
    def test_d_internal_and_wikipedia_dispatch(self, mock_collect):
        """Test D: ExecutionPlan selects internal documents + Wikipedia -> Both execute without duplicate synthesis."""
        mock_coll = MagicMock()
        mock_coll.results = [
            KnowledgeResult(
                provider="wikipedia",
                source_type=SourceType.WIKIPEDIA,
                title="Artificial Intelligence",
                content="Overview of AI...",
                url="https://en.wikipedia.org/wiki/Artificial_intelligence",
                confidence=0.85,
            )
        ]
        mock_collect.return_value = mock_coll

        # Mock internal retrieval
        mock_retrieved = MagicMock()
        mock_retrieved.sources = [
            {"title": "Doc: notes.pdf", "content": "Internal project notes.", "provider": "uploaded_documents", "source_type": "internal_document"}
        ]
        mock_retrieved.confidence = 0.88
        self.orchestrator.retrieval.run = MagicMock(return_value=mock_retrieved)

        plan = ExecutionPlan(
            query="Explain AI based on my notes and Wikipedia",
            source_strategy=SourceStrategy.DOCUMENT_AUGMENTED,
            selected_sources=[SourceType.INTERNAL_DOCUMENT, SourceType.WIKIPEDIA],
            requires_internal_documents=True,
        )

        res = self.orchestrator.dispatch_selected_sources(
            query="Explain AI based on my notes and Wikipedia",
            exec_plan=plan,
            context={},
        )

        self.assertEqual(len(res["doc_sources"]), 1)
        self.assertEqual(res["doc_sources"][0]["provider"], "uploaded_documents")
        self.assertEqual(len(res["external_sources"]), 1)
        self.assertEqual(res["external_sources"][0]["provider"], "wikipedia")

    @patch("core.orchestrator.knowledge_orchestrator.knowledge_orchestrator.collect")
    def test_e_partial_provider_failure(self, mock_collect):
        """Test E: YouTube provider fails/yields 0 results -> Wikipedia still produces usable source collection."""
        # Simulate collection where YouTube failed/returned nothing, but Wikipedia succeeded
        mock_coll = MagicMock()
        mock_coll.results = [
            KnowledgeResult(
                provider="wikipedia",
                source_type=SourceType.WIKIPEDIA,
                title="Machine Learning",
                content="Summary of Machine Learning...",
                url="https://en.wikipedia.org/wiki/Machine_learning",
                confidence=0.85,
            )
        ]
        mock_collect.return_value = mock_coll

        plan = ExecutionPlan(
            query="Learn machine learning",
            source_strategy=SourceStrategy.HYBRID,
            selected_sources=[SourceType.VIDEO, SourceType.WIKIPEDIA],
        )

        res = self.orchestrator.dispatch_selected_sources(
            query="Learn machine learning",
            exec_plan=plan,
            context={},
        )

        ext = res["external_sources"]
        self.assertEqual(len(ext), 1)
        self.assertEqual(ext[0]["provider"], "wikipedia")


if __name__ == "__main__":
    unittest.main()
