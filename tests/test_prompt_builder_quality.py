"""Test suite for EducationalPromptBuilder mode distinction and prompt quality."""

import pytest
from core.models.verification import VerifiedKnowledgeCollection, VerifiedKnowledgeResult
from core.models.domain import SourceType
from core.planner.execution_plan import ExecutionPlan
from core.planner.enums import SourceStrategy, EducationalIntent, ExpectedOutputFormat
from core.synthesis.prompt_builder import EducationalPromptBuilder


def test_case_1_explicit_summary_document_mode():
    """CASE 1: Query 'Summarize my uploaded document' triggers document summary grounding."""
    builder = EducationalPromptBuilder()
    coll = VerifiedKnowledgeCollection(
        query="Summarize my uploaded document.",
        execution_plan_id="p1",
        verification_timestamp="2026-08-18",
        total_latency_ms=10,
        verified_results=[
            VerifiedKnowledgeResult(
                item_id="d1",
                source_type=SourceType.INTERNAL_DOCUMENT,
                provider="uploaded_documents",
                title="study_notes.pdf",
                content="This document covers linear algebra and matrix multiplication.",
                url="",
                verification_score=0.9,
                is_canonical=True,
            )
        ]
    )
    plan = ExecutionPlan(
        intent=EducationalIntent.TOPIC_SUMMARY,
        source_strategy=SourceStrategy.DOCUMENT_ONLY,
        expected_output=ExpectedOutputFormat.SUMMARY,
        target_documents=["study_notes.pdf"]
    )
    prompt = builder.build_synthesis_prompt("Summarize my uploaded document.", coll, plan)

    assert "multi-document summary request" in prompt.lower() or "study_notes.pdf" in prompt or "verified knowledge evidence" in prompt.lower()
    assert "study_notes.pdf" in prompt


def test_case_2_normal_educational_query_with_unrelated_document():
    """CASE 2: Query 'Explain Transformer architecture' with unrelated document does NOT inject refusal directive."""
    builder = EducationalPromptBuilder()
    coll = VerifiedKnowledgeCollection(
        query="Explain Transformer architecture in Machine Learning.",
        execution_plan_id="p2",
        verification_timestamp="2026-08-18",
        total_latency_ms=10,
        verified_results=[
            VerifiedKnowledgeResult(
                item_id="d2",
                source_type=SourceType.INTERNAL_DOCUMENT,
                provider="uploaded_documents",
                title="ai_arch.txt",
                content="Enterprise AI Architecture consists of microservices, API gateways, and vector databases.",
                url="",
                verification_score=0.7,
                is_canonical=True,
            )
        ]
    )
    plan = ExecutionPlan(
        intent=EducationalIntent.CONCEPT_EXPLANATION,
        source_strategy=SourceStrategy.DOCUMENT_ONLY, # planner strategy from keyword match
        expected_output=ExpectedOutputFormat.DETAILED_EXPLANATION,
        target_documents=[] # No explicit target document in user text
    )
    prompt = builder.build_synthesis_prompt("Explain Transformer architecture in Machine Learning.", coll, plan)

    # Must contain Evidence Relevance Protocol
    assert "NORMAL EDUCATIONAL MODE & EVIDENCE RELEVANCE PROTOCOL" in prompt
    assert "DO NOT allow it to block or distort your answer" in prompt
    assert "Problem & Motivation" in prompt


def test_case_3_explicit_strict_document_query_missing_info():
    """CASE 3: Query explicitly requiring strict document mode ('Using only my uploaded document...') injects explicit strict mode."""
    builder = EducationalPromptBuilder()
    coll = VerifiedKnowledgeCollection(
        query="Using only my uploaded document, explain Transformer architecture.",
        execution_plan_id="p3",
        verification_timestamp="2026-08-18",
        total_latency_ms=10,
        verified_results=[
            VerifiedKnowledgeResult(
                item_id="d3",
                source_type=SourceType.INTERNAL_DOCUMENT,
                provider="uploaded_documents",
                title="ai_arch.txt",
                content="Enterprise AI Architecture consists of microservices and vector databases.",
                url="",
                verification_score=0.7,
                is_canonical=True,
            )
        ]
    )
    plan = ExecutionPlan(
        intent=EducationalIntent.CONCEPT_EXPLANATION,
        source_strategy=SourceStrategy.DOCUMENT_ONLY,
        expected_output=ExpectedOutputFormat.DETAILED_EXPLANATION,
        target_documents=["ai_arch.txt"]
    )
    prompt = builder.build_synthesis_prompt("Using only my uploaded document, explain Transformer architecture.", coll, plan)

    assert "EXPLICIT STRICT DOCUMENT MODE" in prompt
    assert "I couldn't find relevant information about your query" in prompt


def test_case_4_general_educational_query_no_evidence():
    """CASE 4: General educational query with no evidence builds rich educational framework."""
    builder = EducationalPromptBuilder()
    coll = VerifiedKnowledgeCollection(
        query="Explain the core concepts of Transformer architectures in Machine Learning.",
        execution_plan_id="p4",
        verification_timestamp="2026-08-18",
        total_latency_ms=10,
        verified_results=[]
    )
    plan = ExecutionPlan(
        intent=EducationalIntent.CONCEPT_EXPLANATION,
        source_strategy=SourceStrategy.GENERAL_KNOWLEDGE,
        expected_output=ExpectedOutputFormat.DETAILED_EXPLANATION,
        target_documents=[]
    )
    prompt = builder.build_synthesis_prompt("Explain the core concepts of Transformer architectures in Machine Learning.", coll, plan)

    assert "No external evidence collected." in prompt
    assert "NORMAL EDUCATIONAL MODE & EVIDENCE RELEVANCE PROTOCOL" in prompt
    assert "Problem & Motivation" in prompt
    assert "Major Components & Architecture" in prompt
