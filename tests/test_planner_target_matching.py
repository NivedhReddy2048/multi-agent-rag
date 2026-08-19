"""Regression test suite for Step 2A — Planner Target Document Matching & Source Strategy Selection."""

import pytest
from core.planner.rules import RuleBasedPlannerEngine
from core.planner.enums import SourceStrategy, EducationalIntent


def test_1_transformer_query_no_false_target_document_match():
    """TEST 1: 'Explain Transformer architectures' must NOT match ai_arch.txt and strategy must be GENERAL_KNOWLEDGE."""
    available_docs = ["ai_arch.txt"]
    query = "Explain the core concepts of Transformer architectures in Machine Learning."

    target_docs = RuleBasedPlannerEngine.resolve_target_documents(query, available_docs)
    assert target_docs == [], f"Expected empty target_docs, got: {target_docs}"

    intent, _ = RuleBasedPlannerEngine.classify_intent(query, [])
    strategy, reason = RuleBasedPlannerEngine.determine_source_strategy(query, intent, [], target_docs=target_docs)

    assert target_docs == []
    assert strategy == SourceStrategy.GENERAL_KNOWLEDGE, f"Expected GENERAL_KNOWLEDGE, got: {strategy} ({reason})"


def test_2_explicit_filename_reference():
    """TEST 2: 'Explain the content of ai_arch.txt' must target ai_arch.txt and choose DOCUMENT_ONLY."""
    available_docs = ["ai_arch.txt"]
    query = "Explain the content of ai_arch.txt"

    target_docs = RuleBasedPlannerEngine.resolve_target_documents(query, available_docs)
    assert "ai_arch.txt" in target_docs

    intent, _ = RuleBasedPlannerEngine.classify_intent(query, [])
    strategy, reason = RuleBasedPlannerEngine.determine_source_strategy(query, intent, [], target_docs=target_docs)

    assert strategy == SourceStrategy.DOCUMENT_ONLY


def test_3_according_to_uploaded_ai_architecture():
    """TEST 3: 'According to my uploaded AI architecture document, explain microservices' must target ai_arch.txt and choose DOCUMENT_ONLY."""
    available_docs = ["ai_arch.txt"]
    query = "According to my uploaded AI architecture document, explain microservices."

    target_docs = RuleBasedPlannerEngine.resolve_target_documents(query, available_docs)
    assert "ai_arch.txt" in target_docs

    intent, _ = RuleBasedPlannerEngine.classify_intent(query, [])
    strategy, reason = RuleBasedPlannerEngine.determine_source_strategy(query, intent, [], target_docs=target_docs)

    assert strategy == SourceStrategy.DOCUMENT_ONLY


def test_4_machine_learning_architecture_query():
    """TEST 4: 'Explain machine learning architecture' must NOT falsely select ai_arch.txt."""
    available_docs = ["ai_arch.txt"]
    query = "Explain machine learning architecture."

    target_docs = RuleBasedPlannerEngine.resolve_target_documents(query, available_docs)
    assert target_docs == [], f"Expected no false match for general 'architecture', got: {target_docs}"

    intent, _ = RuleBasedPlannerEngine.classify_intent(query, [])
    strategy, _ = RuleBasedPlannerEngine.determine_source_strategy(query, intent, [], target_docs=target_docs)

    assert strategy == SourceStrategy.GENERAL_KNOWLEDGE


def test_5_document_summarization_preserves_document_mode():
    """TEST 5: 'Summarize my uploaded study notes' must select DOCUMENT_ONLY."""
    available_docs = ["study_notes.pdf"]
    query = "Summarize my uploaded study notes."

    target_docs = RuleBasedPlannerEngine.resolve_target_documents(query, available_docs)
    intent, _ = RuleBasedPlannerEngine.classify_intent(query, [])
    strategy, _ = RuleBasedPlannerEngine.determine_source_strategy(query, intent, [], target_docs=target_docs)

    assert strategy == SourceStrategy.DOCUMENT_ONLY


def test_6_using_only_my_uploaded_document():
    """TEST 6: 'Using only my uploaded document, explain Transformer architecture' must choose DOCUMENT_ONLY."""
    available_docs = ["ai_arch.txt"]
    query = "Using only my uploaded document, explain Transformer architecture."

    target_docs = RuleBasedPlannerEngine.resolve_target_documents(query, available_docs)
    intent, _ = RuleBasedPlannerEngine.classify_intent(query, [])
    strategy, _ = RuleBasedPlannerEngine.determine_source_strategy(query, intent, [], target_docs=target_docs)

    assert strategy == SourceStrategy.DOCUMENT_ONLY
