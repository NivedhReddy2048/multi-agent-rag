"""Unit and Integration Tests for Step 2C: Retrieval Relevance Gating & Evidence Budgeting."""

import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import Config
from core.verification.knowledge_verifier import KnowledgeVerifier
from core.models.domain import KnowledgeResult, SourceType
from agents.crag import CRAGAgent
from agents.synthesis import SynthesisAgent
from core.planner.execution_plan import ExecutionPlan
from core.planner.enums import EducationalIntent, DifficultyLevel, ExpectedOutputFormat, SourceStrategy

from core.models.verification import VerifiedKnowledgeCollection, VerifiedKnowledgeResult
from core.synthesis.prompt_builder import EducationalPromptBuilder


class TestStep2CRelevanceGating(unittest.TestCase):

    def setUp(self):
        self.cfg = Config()
        self.verifier = KnowledgeVerifier()
        self.crag = CRAGAgent(self.cfg)
        self.synthesis = SynthesisAgent(self.cfg)
        self.default_plan = ExecutionPlan(
            intent=EducationalIntent.CONCEPT_EXPLANATION,
            difficulty=DifficultyLevel.INTERMEDIATE,
            expected_output=ExpectedOutputFormat.DETAILED_EXPLANATION,
            source_strategy=SourceStrategy.GENERAL_KNOWLEDGE,
            target_documents=[]
        )


    def test_1_highly_relevant_chunks_survive(self):
        """TEST 1: Highly relevant positive-score chunks survive filtering."""
        docs = [
            {"content": "Transformer self-attention mechanism with Q, K, V vectors.", "source_file": "transformer.pdf", "score": 6.61}
        ]
        surviving = [d for d in docs if float(d.get("score", 0.0)) >= self.cfg.MIN_RERANK_SCORE]
        self.assertEqual(len(surviving), 1)
        self.assertEqual(surviving[0]["source_file"], "transformer.pdf")

    def test_2_negative_score_chunks_rejected(self):
        """TEST 2: Negative-score irrelevant chunks are rejected."""
        docs = [
            {"content": "Database indexing uses B-trees.", "source_file": "db_notes.pdf", "score": -11.36}
        ]
        surviving = [d for d in docs if float(d.get("score", 0.0)) >= self.cfg.MIN_RERANK_SCORE]
        self.assertEqual(len(surviving), 0)

    def test_3_mixed_collection_filtering(self):
        """TEST 3: Mixed collection (1 relevant + 4 irrelevant) -> only relevant chunk reaches synthesis."""
        docs = [
            {"content": "Transformer architecture relies on self-attention.", "source_file": "transformer.pdf", "score": 7.00},
            {"content": "Database indexing uses B-trees.", "source_file": "db.pdf", "score": -11.38},
            {"content": "Microservices decompose monoliths.", "source_file": "micro.pdf", "score": -7.65},
            {"content": "OS process scheduling algorithms.", "source_file": "os.pdf", "score": -11.32},
            {"content": "Random daily shopping notes.", "source_file": "notes.txt", "score": -11.41},
        ]
        is_sufficient, score = self.crag.evaluate_retrieval("Explain Transformer architecture.", docs)
        self.assertTrue(is_sufficient)
        
        # Test synthesis context preparation
        ctx = {
            "query": "Explain Transformer architecture.",
            "documents": docs,
            "source_strategy": "document_only",
            "execution_plan": self.default_plan,
        }
        prompt, inputs, intent, budgeted_docs, query, source_mode, template, system_msg, telemetry = self.synthesis._prepare_prompt_and_context(ctx)
        self.assertEqual(len(budgeted_docs), 1)
        self.assertEqual(budgeted_docs[0]["source_file"], "transformer.pdf")

    def test_4_all_chunks_below_threshold(self):
        """TEST 4: All chunks below threshold -> empty evidence collection."""
        docs = [
            {"content": "Database indexing uses B-trees.", "source_file": "db.pdf", "score": -11.38},
            {"content": "Microservices decompose monoliths.", "source_file": "micro.pdf", "score": -7.65},
        ]
        is_sufficient, score = self.crag.evaluate_retrieval("Explain Transformer architecture.", docs)
        self.assertFalse(is_sufficient)
        self.assertEqual(score, 0.0)

    def test_5_knowledge_verifier_zero_overlap(self):
        """TEST 5: KnowledgeVerifier zero-overlap query/document relevance returns 0.0, not 0.65."""
        kr = KnowledgeResult(
            query="Explain Transformer architecture.",
            title="Database Notes",
            content="Database indexing uses B-trees and hash indexes.",
            url="",
            provider="uploaded_documents",
            source_type=SourceType.INTERNAL_DOCUMENT,
            metadata={"source_file": "db_notes.pdf"}
        )
        rel = self.verifier._calculate_relevance("Explain Transformer architecture.", kr)
        self.assertEqual(rel, 0.0)

    def test_6_strict_document_only_query_no_evidence(self):
        """TEST 6: Strict DOCUMENT_ONLY query with no surviving evidence preserves strict document behavior."""
        plan = ExecutionPlan(
            intent=EducationalIntent.CONCEPT_EXPLANATION,
            difficulty=DifficultyLevel.INTERMEDIATE,
            expected_output=ExpectedOutputFormat.DETAILED_EXPLANATION,
            source_strategy=SourceStrategy.DOCUMENT_ONLY,
            target_documents=["quantum.pdf"]
        )
        empty_collection = VerifiedKnowledgeCollection(query="Using only my uploaded document, explain quantum entanglement.", verified_results=[])
        builder = EducationalPromptBuilder()
        prompt_str = builder.build_synthesis_prompt(
            query="Using only my uploaded document, explain quantum entanglement.",
            verified_collection=empty_collection,
            plan=plan
        )
        self.assertIn("EXPLICIT STRICT DOCUMENT MODE", prompt_str)
        self.assertIn("couldn't find relevant information about your query", prompt_str)

    def test_7_normal_educational_query_irrelevant_docs(self):
        """TEST 7: Normal educational query with irrelevant docs continues using general knowledge."""
        plan = ExecutionPlan(
            intent=EducationalIntent.CONCEPT_EXPLANATION,
            difficulty=DifficultyLevel.INTERMEDIATE,
            expected_output=ExpectedOutputFormat.DETAILED_EXPLANATION,
            source_strategy=SourceStrategy.GENERAL_KNOWLEDGE,
            target_documents=[]
        )

        empty_collection = VerifiedKnowledgeCollection(query="Explain machine learning.", verified_results=[])
        builder = EducationalPromptBuilder()
        prompt_str = builder.build_synthesis_prompt(
            query="Explain machine learning.",
            verified_collection=empty_collection,
            plan=plan
        )
        self.assertIn("NORMAL EDUCATIONAL MODE", prompt_str)
        self.assertIn("Use general model knowledge", prompt_str)

    def test_8_evidence_chunk_budget_cap(self):
        """TEST 8: Evidence chunk budget cap (MAX_EVIDENCE_CHUNKS = 4)."""
        docs = [
            {"content": f"Relevant Chunk {i}", "source_file": f"doc_{i}.pdf", "score": 10.0 - i} for i in range(10)
        ]
        ctx = {"query": "Explain concept.", "documents": docs, "execution_plan": self.default_plan}
        prompt, inputs, intent, budgeted_docs, query, source_mode, template, system_msg, telemetry = self.synthesis._prepare_prompt_and_context(ctx)
        self.assertLessEqual(len(budgeted_docs), 4)
        self.assertEqual(budgeted_docs[0]["source_file"], "doc_0.pdf")

    def test_9_evidence_character_budget_cap(self):
        """TEST 9: Character budget cap (MAX_EVIDENCE_CHARS = 3000)."""
        docs = [
            {"content": "A" * 2000, "source_file": "doc1.pdf", "score": 9.0},
            {"content": "B" * 2000, "source_file": "doc2.pdf", "score": 8.0},
        ]
        ctx = {"query": "Explain concept.", "documents": docs, "execution_plan": self.default_plan}
        prompt, inputs, intent, budgeted_docs, query, source_mode, template, system_msg, telemetry = self.synthesis._prepare_prompt_and_context(ctx)
        total_chars = sum(len(d["content"]) for d in budgeted_docs)
        self.assertLessEqual(total_chars, 3000)

    def test_10_telemetry_reporting(self):
        """TEST 10: Telemetry correctly reports rejected and surviving chunk counts."""
        docs = [
            {"content": "Good chunk", "source_file": "good.pdf", "score": 5.0},
            {"content": "Bad chunk 1", "source_file": "bad1.pdf", "score": -5.0},
            {"content": "Bad chunk 2", "source_file": "bad2.pdf", "score": -10.0},
        ]
        ctx = {"query": "Explain concept.", "documents": docs, "execution_plan": self.default_plan}
        prompt, inputs, intent, budgeted_docs, query, source_mode, template, system_msg, telemetry = self.synthesis._prepare_prompt_and_context(ctx)
        self.assertEqual(telemetry["synthesis_evidence_chunk_count"], 1)
        self.assertEqual(telemetry["rejected_by_rerank_count"], 2)
        self.assertEqual(telemetry["min_rerank_score_used"], 0.0)



if __name__ == "__main__":
    unittest.main()
