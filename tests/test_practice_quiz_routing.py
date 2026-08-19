"""Regression test suite for EKIP Practice Quiz Intent Classification, Routing, Grounding & Synthesis."""

import unittest
from core.planner.rules import RuleBasedPlannerEngine
from core.planner.enums import EducationalIntent, SourceStrategy, ExpectedOutputFormat
from core.synthesis.prompt_builder import EducationalPromptBuilder
from core.synthesis.knowledge_synthesizer import KnowledgeSynthesizer
from core.models.verification import VerifiedKnowledgeCollection, VerifiedKnowledgeResult
from core.models.domain import SourceType


class TestPracticeQuizRouting(unittest.TestCase):
    """Test suite covering Practice Quiz routing, intent detection, document target resolution, and grounding."""

    def test_intent_classification_variants(self):
        """Verify that all practice quiz query variants are accurately classified under QUIZ_GENERATION."""
        quiz_queries = [
            "Generate 5 practice quiz questions based on my indexed documents.",
            "Create a quiz from my uploaded PDFs.",
            "Test me on my uploaded documents.",
            "Give me 10 MCQs from my notes.",
            "Quiz me on the uploaded Mars document.",
            "Create practice questions from my indexed documents.",
            "Generate a quiz from my uploaded study material.",
            "Generate 5 practice quiz questions on RAG",
        ]

        for query in quiz_queries:
            intent, reason = RuleBasedPlannerEngine.classify_intent(query, [])
            self.assertEqual(
                intent,
                EducationalIntent.QUIZ_GENERATION,
                f"Query '{query}' was classified as {intent} instead of QUIZ_GENERATION. Reason: {reason}"
            )

    def test_source_strategy_routing(self):
        """Verify that practice quiz queries default to SourceStrategy.DOCUMENT_ONLY."""
        queries = [
            "Generate 5 practice quiz questions based on my indexed documents.",
            "Create a quiz from my uploaded PDFs.",
            "Test me on my uploaded documents.",
            "Generate 5 practice quiz questions on RAG",
        ]

        for query in queries:
            intent, _ = RuleBasedPlannerEngine.classify_intent(query, [])
            target_docs = RuleBasedPlannerEngine.resolve_target_documents(query, ["Deep_Solar_System_6_Page_Detailed_Report.pdf"])
            strategy, reason = RuleBasedPlannerEngine.determine_source_strategy(query, intent, [], target_docs=target_docs)

            self.assertEqual(
                strategy,
                SourceStrategy.DOCUMENT_ONLY,
                f"Strategy for '{query}' was {strategy} instead of DOCUMENT_ONLY. Reason: {reason}"
            )

    def test_explicit_document_target_resolution(self):
        """Verify target document resolution for explicit document names and aliases."""
        available_docs = [
            "Deep_Solar_System_6_Page_Detailed_Report.pdf",
            "Coverletter_Stripe.pdf",
            "ai_arch.txt",
            "venus.pdf",
            "MarsReview_merged.pdf"
        ]

        # 1. Explicit Venus PDF
        venus_targets = RuleBasedPlannerEngine.resolve_target_documents("Give me 5 quiz questions from venus.pdf.", available_docs)
        self.assertIn("venus.pdf", venus_targets)

        # 2. Explicit Mars PDF
        mars_targets = RuleBasedPlannerEngine.resolve_target_documents("Quiz me on MarsReview_merged.pdf.", available_docs)
        self.assertIn("MarsReview_merged.pdf", mars_targets)

        # 3. Explicit Solar System PDF
        solar_targets = RuleBasedPlannerEngine.resolve_target_documents("Create 5 questions from the Solar System PDF.", available_docs)
        self.assertIn("Deep_Solar_System_6_Page_Detailed_Report.pdf", solar_targets)

        # 4. Generic Indexed Documents (empty target list -> multi-doc search across all)
        generic_targets = RuleBasedPlannerEngine.resolve_target_documents("Generate 5 practice quiz questions based on my indexed documents.", available_docs)
        self.assertEqual(len(generic_targets), 0, "Generic quiz requests should have empty target_documents to search across all documents.")

    def test_quiz_prompt_builder_format(self):
        """Verify EducationalPromptBuilder constructs a dedicated Quiz Generation prompt with grounding constraints."""
        builder = EducationalPromptBuilder()
        plan = RuleBasedPlannerEngine.generate_plan("Generate 5 practice quiz questions based on my indexed documents.")

        verified_item = VerifiedKnowledgeResult(
            title="Deep_Solar_System_6_Page_Detailed_Report.pdf",
            content="The atmosphere of Venus consists mainly of carbon dioxide with clouds of sulfuric acid. Surface pressure is 92 times that of Earth.",
            source_type=SourceType.INTERNAL_DOCUMENT,
            provider="uploaded_documents",
            verification_score=0.9,
            is_canonical=True,
        )
        collection = VerifiedKnowledgeCollection(
            query="Generate 5 practice quiz questions based on my indexed documents.",
            execution_plan_id="plan_123",
            verification_timestamp="2026-08-15T19:00:00Z",
            total_latency_ms=10.0,
            verified_results=[verified_item],
            overall_confidence=0.9,
        )

        prompt = builder.build_synthesis_prompt("Generate 5 practice quiz questions based on my indexed documents.", collection, plan)

        self.assertIn("Practice Quiz", prompt)
        self.assertIn("EVERY question, option choice (A, B, C, D), and correct answer MUST be directly answerable", prompt)
        self.assertIn("DO NOT write an educational guide, essay, overview, or meta-lesson", prompt)

    def test_insufficient_evidence_grounding_behavior(self):
        """Verify that asking a quiz on an un-indexed topic (e.g. RAG) returns a grounded refusal message."""
        from unittest.mock import patch, MagicMock

        synthesizer = KnowledgeSynthesizer()
        plan = RuleBasedPlannerEngine.generate_plan("Generate 5 practice quiz questions on RAG")

        empty_collection = VerifiedKnowledgeCollection(
            query="Generate 5 practice quiz questions on RAG",
            execution_plan_id="plan_456",
            verification_timestamp="2026-08-15T19:00:00Z",
            total_latency_ms=5.0,
            verified_results=[],
            overall_confidence=0.0,
        )

        # 1. When documents exist in workspace but query has no matching evidence
        mock_engine = MagicMock()
        mock_engine.list_docs.return_value = {"solar_system.pdf": {"chunks": 5, "pages": 2}}

        with patch("core.engine.BaseRAGEngine.get_instance", return_value=mock_engine):
            result = synthesizer.synthesize(empty_collection, plan)
            self.assertIn("couldn't find enough information", result.primary_explanation.lower())
            self.assertNotIn("sentiment analysis", result.primary_explanation.lower())
            self.assertEqual(result.confidence, 0.0)

        # 2. When no documents exist in workspace at all
        mock_engine_empty = MagicMock()
        mock_engine_empty.list_docs.return_value = {}

        with patch("core.engine.BaseRAGEngine.get_instance", return_value=mock_engine_empty):
            result_empty = synthesizer.synthesize(empty_collection, plan)
            self.assertIn("no uploaded or indexed documents were found", result_empty.primary_explanation.lower())
            self.assertEqual(result_empty.confidence, 0.0)



if __name__ == "__main__":
    unittest.main()
