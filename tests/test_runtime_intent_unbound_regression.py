"""
Regression Test Suite: EKIP Runtime Intent Unbound Variable Verification.

Tests all execution paths in OrchestratorAgent and dispatch_selected_sources:
1. General knowledge query with no documents (requires_docs=False).
2. Document query with available documents.
3. External/web/research query.
4. Path where document retrieval is skipped but external evidence collection executes.
"""

import pytest
from unittest.mock import MagicMock
from config.settings import Config
from agents.orchestrator import OrchestratorAgent
from core.planner.execution_plan import ExecutionPlan
from core.planner.enums import EducationalIntent, SourceStrategy, DocumentUsageMode
from core.models.domain import SourceType


@pytest.fixture
def mock_orchestrator():
    mock_engine = MagicMock()
    mock_memory = MagicMock()
    mock_retrieval = MagicMock()
    mock_synthesis = MagicMock()

    orch = OrchestratorAgent(Config, mock_engine, mock_memory)
    orch.retrieval = mock_retrieval
    orch.synthesis = mock_synthesis
    return orch


def test_general_knowledge_no_docs_unbound_intent_regression(mock_orchestrator):
    """
    Test 1: General knowledge query with no documents (requires_docs=False).
    Guarantees dispatch_selected_sources does not raise UnboundLocalError for intent.
    """
    exec_plan = ExecutionPlan(
        query="Explain the core concepts of Transformer architectures in Machine Learning.",
        intent=EducationalIntent.CONCEPT_EXPLANATION,
        source_strategy=SourceStrategy.GENERAL_KNOWLEDGE,
        document_usage_mode=DocumentUsageMode.EXCLUDED,
        selected_sources=[SourceType.WIKIPEDIA],
    )

    ctx = {
        "query": "Explain the core concepts of Transformer architectures in Machine Learning.",
        "execution_plan": exec_plan,
        "documents": [],
        "filters": {},
        "request_id": "test_gen_know",
    }

    # Execute dispatch_selected_sources directly to verify variable scope
    res = mock_orchestrator.dispatch_selected_sources(
        query=ctx["query"],
        exec_plan=exec_plan,
        context=ctx,
    )

    assert res["requires_docs"] is False
    assert res["doc_retrieval_executed"] is False
    assert isinstance(res["external_sources"], list)


def test_document_query_with_documents(mock_orchestrator):
    """
    Test 2: Document query with available documents.
    """
    exec_plan = ExecutionPlan(
        query="Summarize my uploaded document.",
        intent=EducationalIntent.DOCUMENT_QUERY,
        source_strategy=SourceStrategy.DOCUMENT_ONLY,
        document_usage_mode=DocumentUsageMode.REQUIRED,
        selected_sources=[SourceType.INTERNAL_DOCUMENT],
    )

    mock_orchestrator.retrieval.run.return_value = MagicMock(
        sources=[{"content": "Doc snippet 1", "source_type": "internal_document"}],
        confidence=85.0,
    )

    ctx = {
        "query": "Summarize my uploaded document.",
        "execution_plan": exec_plan,
        "documents": [],
        "filters": {},
        "request_id": "test_doc_query",
    }

    res = mock_orchestrator.dispatch_selected_sources(
        query=ctx["query"],
        exec_plan=exec_plan,
        context=ctx,
    )

    assert res["requires_docs"] is True
    assert res["doc_retrieval_executed"] is True
    assert len(res["doc_sources"]) == 1


def test_external_research_query(mock_orchestrator):
    """
    Test 3: External/web/research query.
    """
    exec_plan = ExecutionPlan(
        query="Find research papers on quantum computing.",
        intent=EducationalIntent.RESEARCH_DISCOVERY,
        source_strategy=SourceStrategy.RESEARCH,
        document_usage_mode=DocumentUsageMode.EXCLUDED,
        selected_sources=[SourceType.ARXIV, SourceType.SEMANTIC_SCHOLAR],
    )

    ctx = {
        "query": "Find research papers on quantum computing.",
        "execution_plan": exec_plan,
        "documents": [],
        "filters": {},
        "request_id": "test_research_query",
    }

    res = mock_orchestrator.dispatch_selected_sources(
        query=ctx["query"],
        exec_plan=exec_plan,
        context=ctx,
    )

    assert res["requires_docs"] is False
    assert res["doc_retrieval_executed"] is False
    assert isinstance(res["external_sources"], list)


def test_doc_retrieval_skipped_external_executes(mock_orchestrator):
    """
    Test 4: Path where document retrieval is skipped (requires_docs=False)
    but external evidence collection executes (selected_sources contains non-internal sources).
    """
    exec_plan = ExecutionPlan(
        query="What are the latest updates on Python 3.13?",
        intent=EducationalIntent.FACTUAL_LOOKUP,
        source_strategy=SourceStrategy.WEB_AUGMENTED,
        document_usage_mode=DocumentUsageMode.EXCLUDED,
        selected_sources=[SourceType.TRUSTED_WEB],
    )

    ctx = {
        "query": "What are the latest updates on Python 3.13?",
        "execution_plan": exec_plan,
        "documents": [],
        "filters": {},
        "request_id": "test_skip_doc_exec_ext",
    }

    res = mock_orchestrator.dispatch_selected_sources(
        query=ctx["query"],
        exec_plan=exec_plan,
        context=ctx,
    )

    assert res["requires_docs"] is False
    assert res["doc_retrieval_executed"] is False
    assert isinstance(res["external_sources"], list)
