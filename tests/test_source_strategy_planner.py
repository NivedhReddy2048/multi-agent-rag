"""Regression and Unit Test Suite for EKIP Intent-Driven Source Planning & Retrieval Strategy."""

import pytest
from core.planner.enums import (
    EducationalIntent,
    DifficultyLevel,
    SourceStrategy,
    RetrievalStrategy,
)
from core.planner.rules import RuleBasedPlannerEngine
from core.planner.execution_plan import ExecutionPlan
from core.models.domain import SourceType
from core.orchestrator.knowledge_orchestrator import knowledge_orchestrator
from core.synthesis.knowledge_synthesizer import knowledge_synthesizer
from core.models.verification import VerifiedKnowledgeCollection


def test_general_educational_question_no_document_retrieval():
    """Verify general educational questions do NOT trigger document retrieval."""
    general_queries = [
        "Explain Transformer architecture",
        "What is Machine Learning?",
        "Explain SQL joins",
        "What is Kubernetes?",
        "Explain Operating Systems",
    ]

    for query in general_queries:
        plan = RuleBasedPlannerEngine.generate_plan(query)
        assert plan.source_strategy == SourceStrategy.GENERAL_KNOWLEDGE, f"Failed for query: {query}"
        assert SourceType.INTERNAL_DOCUMENT not in plan.selected_sources, f"Internal document present for: {query}"
        assert plan.requires_internal_documents is False, f"requires_internal_documents True for: {query}"


def test_uploaded_document_question_triggers_document_retrieval():
    """Verify document-specific queries trigger DOCUMENT_ONLY or DOCUMENT_AUGMENTED strategy."""
    doc_queries = [
        "Summarize my uploaded notes",
        "Explain this PDF",
        "Search my documents",
        "What does my report say?",
        "Answer using my uploaded notes",
        "Find information in my workspace",
    ]

    for query in doc_queries:
        plan = RuleBasedPlannerEngine.generate_plan(query)
        assert plan.source_strategy in (SourceStrategy.DOCUMENT_ONLY, SourceStrategy.DOCUMENT_AUGMENTED)
        assert SourceType.INTERNAL_DOCUMENT in plan.selected_sources
        assert plan.requires_internal_documents is True


def test_hybrid_question_combines_sources():
    """Verify hybrid queries referencing both uploaded notes and general concepts use DOCUMENT_AUGMENTED strategy."""
    query = "Compare my uploaded lecture notes with standard Transformer architecture"
    plan = RuleBasedPlannerEngine.generate_plan(query)

    assert plan.source_strategy == SourceStrategy.DOCUMENT_AUGMENTED
    assert SourceType.INTERNAL_DOCUMENT in plan.selected_sources
    assert SourceType.GENERAL_AI in plan.selected_sources or SourceType.WIKIPEDIA in plan.selected_sources
    assert plan.requires_internal_documents is True


def test_research_question_selects_research_providers():
    """Verify research queries select RESEARCH strategy and academic paper providers."""
    query = "What are recent research papers on diffusion models in arXiv?"
    plan = RuleBasedPlannerEngine.generate_plan(query)

    assert plan.source_strategy == SourceStrategy.RESEARCH
    assert any(s in plan.selected_sources for s in [SourceType.SEMANTIC_SCHOLAR, SourceType.ARXIV])
    assert SourceType.INTERNAL_DOCUMENT not in plan.selected_sources
    assert plan.requires_research is True


def test_empty_workspace_answers_correctly_without_failing():
    """Verify empty collection or general questions generate complete educational answer without failing."""
    empty_collection = VerifiedKnowledgeCollection(
        query="What is Kubernetes?",
        verified_results=[],
        overall_confidence=0.0,
        overall_agreement=0.0,
    )

    plan = RuleBasedPlannerEngine.generate_plan("What is Kubernetes?")
    syn = knowledge_synthesizer.synthesize(empty_collection, plan=plan)

    assert syn.primary_explanation != ""
    assert "cannot answer" not in syn.primary_explanation.lower()
    assert "do not contain" not in syn.primary_explanation.lower()
    assert syn.confidence > 0.0


def test_orchestrator_skips_document_agent_for_general_knowledge():
    """Verify KnowledgeOrchestrator skips DocumentKnowledgeAgent when GENERAL_KNOWLEDGE strategy is active."""
    plan = RuleBasedPlannerEngine.generate_plan("Explain SQL joins")

    collection = knowledge_orchestrator.collect("Explain SQL joins", plan)

    assert "internal_document" not in collection.sources_requested
    assert "internal_document" not in collection.sources_completed
