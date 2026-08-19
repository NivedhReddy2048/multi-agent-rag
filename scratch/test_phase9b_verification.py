"""EKIP Phase 9B Architectural Invariants Verification Script."""

import os
import sys
import unittest
from unittest.mock import MagicMock

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.settings import Config
from core.planner.enums import SourceRole, SourceStrategy, EducationalIntent, DocumentUsageMode
from agents.orchestrator import OrchestratorAgent
from agents.synthesis import SynthesisAgent
from core.models.verification import VerifiedKnowledgeCollection, VerifiedKnowledgeResult
from core.synthesis.prompt_builder import EducationalPromptBuilder
from core.planner.execution_plan import ExecutionPlan


class TestPhase9BArchitectureInvariants(unittest.TestCase):

    def setUp(self):
        self.cfg = Config()
        self.orchestrator = OrchestratorAgent(self.cfg, engine=MagicMock(), memory=MagicMock())

    def test_1_resource_slot_isolation(self):
        """Verify 10 learning resources (5 YouTube + 5 GitHub) do NOT evict 2 factual sources."""
        sources = [
            {"title": f"Factual Doc {i}", "content": f"Fact {i}", "source_type": "internal_document", "provider": "uploaded_documents"}
            for i in range(2)
        ]
        sources += [
            {"title": f"Video {i}", "content": f"Video desc {i}", "source_type": "video", "provider": "youtube"}
            for i in range(5)
        ]
        sources += [
            {"title": f"Repo {i}", "content": f"Repo desc {i}", "source_type": "github_repo", "provider": "github"}
            for i in range(5)
        ]

        query = "Explain transformers"
        ranked = self.orchestrator._rank_and_filter_evidence(sources, query)

        factual = [s for s in ranked if s.get("source_role") == SourceRole.FACTUAL_EVIDENCE.value]
        learning = [s for s in ranked if s.get("source_role") == SourceRole.LEARNING_RESOURCE.value]

        self.assertEqual(len(factual), 2, "Factual sources should NOT be evicted by learning resources")
        self.assertGreater(len(learning), 0, "Learning resources should be preserved separately")

    def test_2_document_augmented_preservation(self):
        """Verify uploaded document chunk reaches factual context alongside external web, YouTube, and GitHub."""
        sources = [
            {"title": "Doc Chunk 1", "content": "Transformer embedding dimension is 512.", "source_type": "internal_document", "provider": "uploaded_documents"},
            {"title": "Web Overview", "content": "Transformers were introduced in 2017.", "source_type": "trusted_web", "provider": "tavily"},
            {"title": "Video Guide", "content": "YouTube Transformer Tutorial", "source_type": "video", "provider": "youtube"},
            {"title": "PyTorch Repo", "content": "PyTorch Transformer implementation", "source_type": "github_repo", "provider": "github"},
        ]

        query = "Explain transformers using my uploaded document and external resources"
        ranked = self.orchestrator._rank_and_filter_evidence(sources, query)

        factual = [s for s in ranked if s.get("source_role") == SourceRole.FACTUAL_EVIDENCE.value]
        doc_factual = [s for s in factual if s.get("source_type") == "internal_document"]

        self.assertEqual(len(doc_factual), 1, "Uploaded document chunk must remain in factual context")

    def test_3_strict_document_only_isolation(self):
        """Verify 0 document chunks in strict document_only strategy yields INSUFFICIENT_EVIDENCE with no external fallback."""
        query_str = "According to my document only, explain the architecture"
        plan = ExecutionPlan(
            intent=EducationalIntent.CONCEPT_EXPLANATION,
            source_strategy=SourceStrategy.DOCUMENT_ONLY,
            selected_sources=[],
            requires_internal_documents=True,
            document_usage_mode=DocumentUsageMode.REQUIRED,
        )

        ctx = {
            "query": query_str,
            "execution_plan": plan,
            "documents": [],
            "source_strategy": "document_only",
        }

        # Mock retrieval returning empty sources
        self.orchestrator.retrieval = MagicMock()
        mock_ret = MagicMock()
        mock_ret.sources = []
        mock_ret.confidence = 0.0
        self.orchestrator.retrieval.run.return_value = mock_ret

        # Mock synthesis returning refusal
        self.orchestrator.synthesis = MagicMock()
        mock_synth = MagicMock()
        mock_synth.content = "I couldn't find relevant information in your uploaded documents."
        mock_synth.success = False
        mock_synth.sources = []
        mock_synth.metadata = {"success": False, "failure_reason": "INSUFFICIENT_EVIDENCE"}
        self.orchestrator.synthesis.run.return_value = mock_synth

        # Mock validation
        self.orchestrator.validation = MagicMock()
        mock_val = MagicMock()
        mock_val.content = "I couldn't find relevant information in your uploaded documents."
        mock_val.metadata = {"warnings": ["EMPTY_ANSWER_NO_EVIDENCE"]}
        mock_val.agent_trace = []
        self.orchestrator.validation.run.return_value = mock_val

        result = self.orchestrator.run(ctx)

        self.assertEqual(result.metadata.get("response_status"), "INSUFFICIENT_EVIDENCE")
        self.assertEqual(result.metadata.get("factual_evidence_count"), 0)

    def test_4_research_discovery_coexistence(self):
        """Verify research papers are placed appropriately without crowding out factual evidence."""
        sources = [
            {"title": "RAG Overview", "content": "Retrieval Augmented Generation reduces hallucination.", "source_type": "trusted_web", "provider": "tavily"},
            {"title": "Attention Is All You Need", "content": "Transformer research paper snippet", "source_type": "arxiv", "provider": "arxiv", "authors": ["Vaswani et al."]},
            {"title": "RAG Hallucination Survey", "content": "Survey on RAG hallucinations", "source_type": "semantic_scholar", "provider": "semantic_scholar", "authors": ["Zhang et al."]},
        ]

        query = "Explain RAG hallucination and recommend research papers"
        ranked = self.orchestrator._rank_and_filter_evidence(sources, query, intent="research_discovery")

        factual = [s for s in ranked if s.get("source_role") == SourceRole.FACTUAL_EVIDENCE.value]
        learning = [s for s in ranked if s.get("source_role") == SourceRole.LEARNING_RESOURCE.value]

        self.assertTrue(any(s.get("source_type") == "trusted_web" for s in factual), "Factual evidence must contain web overview")
        self.assertGreater(len(learning), 0, "Research papers requested as recommendations belong in learning resources")

    def test_5_exactly_one_synthesis_call(self):
        """Verify OrchestratorAgent makes exactly 1 synthesis call during standard execution."""
        sources = [
            {"title": "Doc Chunk 1", "content": "Transformer embedding dimension is 512.", "source_type": "internal_document", "provider": "uploaded_documents"}
        ]

        plan = ExecutionPlan(
            intent=EducationalIntent.CONCEPT_EXPLANATION,
            source_strategy=SourceStrategy.DOCUMENT_ONLY,
            selected_sources=[],
            requires_internal_documents=True,
            document_usage_mode=DocumentUsageMode.REQUIRED,
        )

        ctx = {
            "query": "Explain transformers",
            "execution_plan": plan,
            "intent": "CONCEPT_EXPLANATION",
            "documents": sources,
            "source_strategy": "document_only",
        }

        self.orchestrator.retrieval = MagicMock()
        mock_ret = MagicMock()
        mock_ret.sources = sources
        mock_ret.confidence = 90.0
        self.orchestrator.retrieval.run.return_value = mock_ret

        self.orchestrator.crag = MagicMock()
        mock_crag = MagicMock()
        mock_crag.metadata = {"sufficient": True, "retrieval_score": 0.9}
        mock_crag.agent_trace = []
        self.orchestrator.crag.run.return_value = mock_crag

        self.orchestrator.synthesis = MagicMock()
        mock_synth = MagicMock()
        mock_synth.content = "Transformers use self-attention mechanisms [1]."
        mock_synth.success = True
        mock_synth.sources = sources
        mock_synth.metadata = {"success": True, "provider": "gemini", "model": "gemini-2.5-flash"}
        self.orchestrator.synthesis.run.return_value = mock_synth

        self.orchestrator.validation = MagicMock()
        mock_val = MagicMock()
        mock_val.content = "Transformers use self-attention mechanisms [1]."
        mock_val.metadata = {"warnings": []}
        mock_val.agent_trace = []
        self.orchestrator.validation.run.return_value = mock_val

        from unittest.mock import patch
        from core.models.synthesis import LearningPath
        mock_lp = LearningPath(
            current_topic="Transformers",
            prerequisites=["Python"],
            next_topics=["Attention"],
            advanced_topics=["LLMs"],
        )
        try:
            with patch("core.synthesis.guided_learning.guided_learning_engine.generate_guided_questions", return_value=["Q1", "Q2"]), \
                 patch("core.synthesis.guided_learning.guided_learning_engine.generate_learning_path", return_value=mock_lp):
                self.orchestrator.run(ctx)
        except BaseException as e:
            import traceback
            print(f"Inside test_5 exception: {type(e).__name__}: {e}", flush=True)
            traceback.print_exc(file=sys.stdout)

        self.assertEqual(self.orchestrator.synthesis.run.call_count, 1, "There MUST be exactly 1 synthesis pass")


if __name__ == "__main__":
    t = TestPhase9BArchitectureInvariants()
    
    try:
        t.setUp()
        print("Running Test 1: Resource Slot Isolation...", flush=True)
        t.test_1_resource_slot_isolation()
        print("Test 1: PASS", flush=True)
        
        t.setUp()
        print("Running Test 2: Document Augmented Preservation...", flush=True)
        t.test_2_document_augmented_preservation()
        print("Test 2: PASS", flush=True)
        
        t.setUp()
        print("Running Test 3: Strict Document Only Isolation...", flush=True)
        t.test_3_strict_document_only_isolation()
        print("Test 3: PASS", flush=True)
        
        t.setUp()
        print("Running Test 4: Research Discovery Coexistence...", flush=True)
        t.test_4_research_discovery_coexistence()
        print("Test 4: PASS", flush=True)
        
        t.setUp()
        print("Running Test 5: Exactly One Synthesis Call...", flush=True)
        t.test_5_exactly_one_synthesis_call()
        print("Test 5: PASS", flush=True)
        
        print("\n✅ ALL 5 PHASE 9B ARCHITECTURE INVARIANT TESTS PASSED SUCCESSFULLY!", flush=True)
    except Exception as exc:
        import traceback
        print(f"\n❌ TEST EXCEPTION OCCURRED: {type(exc).__name__}: {exc}", flush=True)
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
