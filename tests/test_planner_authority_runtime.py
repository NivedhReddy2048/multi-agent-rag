"""Automated Regression Suite for Planner Authority & Runtime Source Selection."""

import pytest
from typing import Dict, Any, List
from config import Config
from core.planner.enums import SourceStrategy
from core.models.domain import SourceType
from core.planner.rules import RuleBasedPlannerEngine
from agents.orchestrator import OrchestratorAgent
from agents.base import AgentResult


class MockDoc:
    def __init__(self, content="This document discusses deep learning concepts.", source="lecture_notes.pdf", page=1, chunk_id="c1", score=0.88):
        self.page_content = content
        self.metadata = {"source_file": source, "page_number": page, "chunk_id": chunk_id, "score": score}


class DummyEngine:
    """Mock engine simulating workspace with or without documents."""
    def __init__(self, has_docs: bool = True):
        self.has_docs = has_docs
        self.doc_count = 5 if has_docs else 0
        self.cfg = type("Cfg", (), {"RERANK_TOP_K": 5})()

    def list_docs(self) -> Dict[str, Any]:
        if not self.has_docs:
            return {}
        return {"lecture_notes.pdf": {"chunks": 12, "pages": 5}}

    def dense_search(self, query: str, k: int = 8, **kwargs) -> List[Any]:
        if not self.has_docs:
            return []
        return [MockDoc()]

    def sparse_search(self, query: str, k: int = 8, **kwargs) -> List[Any]:
        if not self.has_docs:
            return []
        return [MockDoc()]

    def reciprocal_rank_fusion(self, dense, sparse) -> List[Any]:
        return dense or sparse

    def rerank(self, query, fused, top_k=5) -> List[Any]:
        return fused

    def compress_context(self, reranked, max_chunks=6) -> List[Any]:
        return reranked

    def confidence(self) -> float:
        return 88.0 if self.has_docs else 0.0


class DummyMemory:
    """Mock conversation memory."""
    def record_query_metrics(self, **kwargs):
        pass
    def log_query_analytics(self, **kwargs):
        pass


@pytest.fixture
def mock_orchestrator():
    engine = DummyEngine(has_docs=True)
    memory = DummyMemory()
    orch = OrchestratorAgent(Config, engine, memory)
    return orch, engine


def test_general_educational_question_skips_document_retrieval(mock_orchestrator):
    """General educational questions must select GENERAL_KNOWLEDGE and skip document retrieval."""
    orch, engine = mock_orchestrator
    query = "Explain the core concepts of Transformer architectures in Machine Learning."

    from unittest.mock import patch
    from core.llm.base_provider import LLMResponse
    mock_resp = LLMResponse(provider="mock", model="mock", content="Transformers are neural network architectures based on self-attention mechanisms.", latency=10.0, tokens=50, success=True, error="")

    with patch.object(orch.llm_manager, "generate", return_value=mock_resp):
        result = orch.run({"query": query, "history": []})

    meta = result.metadata
    assert meta["planner_source_strategy"] == "general_knowledge"
    assert meta["runtime_source_strategy"] == "general_knowledge"
    assert meta["was_planner_overridden"] is False
    assert meta["document_retrieval_executed"] is False
    assert meta["retrieved_chunks_count"] == 0
    assert result.success is True
    assert len(result.content) > 50


def test_documents_exist_but_planner_selects_general_knowledge(mock_orchestrator):
    """Even if indexed documents exist in workspace, general queries must NOT execute document retrieval."""
    orch, engine = mock_orchestrator
    assert engine.has_docs is True  # Confirm documents exist in store

    query = "What is Kubernetes?"
    result = orch.run({"query": query, "history": []})

    meta = result.metadata
    assert meta["planner_source_strategy"] == "general_knowledge"
    assert meta["document_retrieval_executed"] is False
    assert meta["retrieved_chunks_count"] == 0
    assert "Skipping Document Retrieval" in " ".join(result.agent_trace)


def test_document_summary_request_executes_document_retrieval(mock_orchestrator):
    """Queries explicitly requesting uploaded notes/documents must trigger document retrieval."""
    orch, engine = mock_orchestrator
    query = "Summarize my uploaded lecture notes."

    result = orch.run({"query": query, "history": []})

    meta = result.metadata
    assert meta["planner_source_strategy"] in ("document_only", "document_augmented")
    assert meta["document_retrieval_executed"] is True
    assert meta["retrieved_chunks_count"] > 0
    assert result.success is True


def test_hybrid_request_uses_documents_and_llm(mock_orchestrator):
    """Hybrid queries comparing uploaded notes with external concepts must execute document retrieval and combine."""
    orch, engine = mock_orchestrator
    query = "Compare my uploaded lecture notes with standard Transformer architecture."

    result = orch.run({"query": query, "history": []})

    meta = result.metadata
    assert meta["planner_source_strategy"] in ("document_augmented", "hybrid")
    assert meta["document_retrieval_executed"] is True
    assert meta["retrieved_chunks_count"] > 0
    assert result.success is True


def test_empty_retrieval_triggers_automatic_downgrade_without_failure():
    """If document retrieval is requested but returns 0 chunks, EKIP must automatically downgrade strategy to GENERAL_KNOWLEDGE."""
    engine = DummyEngine(has_docs=False)  # Workspace has 0 documents matching
    memory = DummyMemory()
    orch = OrchestratorAgent(Config, engine, memory)

    # Document augmented request
    plan = RuleBasedPlannerEngine.generate_plan("Compare deep learning with my uploaded notes", [])
    plan.source_strategy = SourceStrategy.DOCUMENT_AUGMENTED

    result = orch.run({
        "query": "Compare deep learning with my uploaded notes",
        "history": [],
        "execution_plan": plan,
    })

    meta = result.metadata
    assert meta["planner_source_strategy"] == "document_augmented"
    assert meta["runtime_source_strategy"] == "general_knowledge"  # Automatic downgrade
    assert meta["document_retrieval_executed"] is True
    assert meta["retrieved_chunks_count"] == 0
    assert result.success is True
    assert "The indexed documents do not contain enough information" not in result.content


def test_existing_document_workflows_remain_functional(mock_orchestrator):
    """Ensure standard RAG workflows remain functional for document-specific questions."""
    orch, engine = mock_orchestrator
    query = "What does my PDF report say about deep learning?"

    result = orch.run({"query": query, "history": []})
    assert result.success is True
    assert result.metadata["document_retrieval_executed"] is True
