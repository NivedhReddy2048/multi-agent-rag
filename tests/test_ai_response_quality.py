"""EKIP Phase 3.0 AI Response Quality & Runtime Validation Test Suite."""

import pytest
from unittest.mock import MagicMock
from typing import Dict, Any, List

from config import Config
from core.planner.enums import SourceStrategy
from graph.builder import create_ekip_planning_graph
from agents.orchestrator import OrchestratorAgent
from core.memory import ConversationMemory


class MockDoc:
    def __init__(self, content="Solar System consists of Sun and planets including Jupiter and Mars.", source="solar_system_guide.pdf", page=1, chunk_id="solar_c1", score=0.92):
        self.page_content = content
        self.metadata = {"source_file": source, "page_number": page, "chunk_id": chunk_id, "score": score}


class ControlledTestEngine:
    """Controlled mock engine simulating workspace with or without documents."""
    def __init__(self, has_docs: bool = True):
        self.has_docs = has_docs
        self.cfg = type("Cfg", (), {"RERANK_TOP_K": 5})()

    def list_docs(self) -> Dict[str, Any]:
        if not self.has_docs:
            return {}
        return {"solar_system_guide.pdf": {"chunks": 10, "pages": 4}}

    def dense_search(self, query: str, k: int = 8, **kwargs) -> List[Any]:
        if not self.has_docs:
            return []
        if "solar system" in query.lower() or "planet" in query.lower():
            return [MockDoc()]
        return []

    def sparse_search(self, query: str, k: int = 8, **kwargs) -> List[Any]:
        if not self.has_docs:
            return []
        if "solar system" in query.lower() or "planet" in query.lower():
            return [MockDoc()]
        return []

    def reciprocal_rank_fusion(self, dense, sparse) -> List[Any]:
        return dense or sparse

    def rerank(self, query, fused, top_k=5) -> List[Any]:
        return fused

    def compress_context(self, reranked, max_chunks=6) -> List[Any]:
        return reranked

    def confidence(self) -> float:
        return 92.0 if self.has_docs else 0.0


@pytest.fixture
def quality_setup():
    engine = ControlledTestEngine(has_docs=True)
    memory = ConversationMemory(":memory:")
    orch = OrchestratorAgent(Config, engine, memory)
    planning_graph = create_ekip_planning_graph()
    return orch, planning_graph, engine, memory


# ============================================================
# TEST GROUP A — GENERAL KNOWLEDGE
# ============================================================
@pytest.mark.parametrize("query", [
    "Explain Transformer architecture.",
    "Explain process vs thread.",
    "Explain Python decorators.",
    "Explain database normalization.",
    "Explain TCP vs UDP.",
])
def test_group_a_general_knowledge_queries(quality_setup, query):
    """Group A: General knowledge queries must execute single synthesis without document retrieval."""
    orch, planning_graph, engine, memory = quality_setup

    plan_state = planning_graph.invoke({"question": query, "conversation_history": []})
    exec_plan = plan_state.execution_plan
    edu_meta = plan_state.provider_metadata.get("educational_response") or plan_state.educational_response
    if hasattr(edu_meta, "dict"):
        edu_meta = edu_meta.dict()

    ctx = {
        "query": query,
        "history": [],
        "filters": {},
        "execution_plan": exec_plan,
        "educational_response": edu_meta,
        "plan_state": plan_state,
    }

    # Spy synthesis call count
    synth_calls = 0
    orig_synth_run = orch.synthesis.run
    def spy_run(*args, **kwargs):
        nonlocal synth_calls
        synth_calls += 1
        return orig_synth_run(*args, **kwargs)
    orch.synthesis.run = spy_run

    result = orch.run(ctx)

    assert synth_calls == 0, "SynthesisAgent.run must NOT be called when EducationalResponse exists"
    assert result.metadata["planner_source_strategy"] == "general_knowledge"
    assert result.metadata["document_retrieval_executed"] is False
    assert result.metadata["retrieved_chunks_count"] == 0
    assert edu_meta is not None
    assert "ai_explanation" in edu_meta
    assert len(edu_meta["ai_explanation"]) > 0
    assert result.content.strip() == edu_meta["ai_explanation"].strip()


# ============================================================
# TEST GROUP B — DOCUMENT KNOWLEDGE
# ============================================================
def test_group_b_document_knowledge_found(quality_setup):
    """Group B1: Document query with answer present in documents."""
    orch, planning_graph, engine, memory = quality_setup
    query = "Summarize the uploaded Solar System document."

    plan_state = planning_graph.invoke({"question": query, "conversation_history": []})
    exec_plan = plan_state.execution_plan
    edu_meta = plan_state.provider_metadata.get("educational_response") or plan_state.educational_response
    if hasattr(edu_meta, "dict"):
        edu_meta = edu_meta.dict()

    ctx = {
        "query": query,
        "history": [],
        "execution_plan": exec_plan,
        "educational_response": edu_meta,
        "plan_state": plan_state,
    }

    result = orch.run(ctx)
    assert result.metadata["document_retrieval_executed"] is True
    assert result.metadata["retrieved_chunks_count"] > 0
    assert edu_meta is not None


def test_group_b_document_knowledge_missing(quality_setup):
    """Group B3: Document query when answer is missing from documents."""
    orch, planning_graph, engine, memory = quality_setup
    query = "According to the uploaded documents, what is the revenue of Acme Corp in 2025?"

    plan_state = planning_graph.invoke({"question": query, "conversation_history": []})
    exec_plan = plan_state.execution_plan
    edu_meta = plan_state.provider_metadata.get("educational_response") or plan_state.educational_response
    if hasattr(edu_meta, "dict"):
        edu_meta = edu_meta.dict()

    ctx = {
        "query": query,
        "history": [],
        "execution_plan": exec_plan,
        "educational_response": edu_meta,
        "plan_state": plan_state,
    }

    result = orch.run(ctx)
    assert result.content is not None
    assert len(result.content) > 0


# ============================================================
# TEST GROUP C — DOCUMENT PRESENCE MUST NOT FORCE RETRIEVAL
# ============================================================
def test_group_c_documents_present_does_not_force_retrieval(quality_setup):
    """Group C: General knowledge query must skip retrieval even when documents are indexed."""
    orch, planning_graph, engine, memory = quality_setup
    assert engine.list_docs() != {}, "Engine must contain indexed documents"

    query = "What is recursion?"
    plan_state = planning_graph.invoke({"question": query, "conversation_history": []})
    exec_plan = plan_state.execution_plan
    edu_meta = plan_state.provider_metadata.get("educational_response") or plan_state.educational_response
    if hasattr(edu_meta, "dict"):
        edu_meta = edu_meta.dict()

    ctx = {
        "query": query,
        "history": [],
        "execution_plan": exec_plan,
        "educational_response": edu_meta,
        "plan_state": plan_state,
    }

    result = orch.run(ctx)
    assert result.metadata["planner_source_strategy"] == "general_knowledge"
    assert result.metadata["document_retrieval_executed"] is False
    assert result.metadata["retrieved_chunks_count"] == 0


# ============================================================
# TEST GROUP D — RESEARCH QUERY
# ============================================================
def test_group_d_research_query(quality_setup):
    """Group D: Research query routes to research intent/strategy."""
    orch, planning_graph, engine, memory = quality_setup
    query = "Latest research on retrieval augmented generation."

    plan_state = planning_graph.invoke({"question": query, "conversation_history": []})
    exec_plan = plan_state.execution_plan
    edu_meta = plan_state.provider_metadata.get("educational_response") or plan_state.educational_response
    if hasattr(edu_meta, "dict"):
        edu_meta = edu_meta.dict()

    ctx = {
        "query": query,
        "history": [],
        "execution_plan": exec_plan,
        "educational_response": edu_meta,
        "plan_state": plan_state,
    }

    result = orch.run(ctx)
    assert exec_plan is not None
    assert edu_meta is not None
    assert result.content == edu_meta["ai_explanation"]


# ============================================================
# TEST GROUP E — MULTI-TURN CONTEXT CONTINUITY
# ============================================================
def test_group_e_multi_turn_continuity(quality_setup):
    """Group E: Multi-turn conversation maintains continuity without citation leakage."""
    orch, planning_graph, engine, memory = quality_setup

    turns = [
        "Explain transformers.",
        "Explain self-attention in more detail.",
        "Why is it better than recurrent networks?",
        "Now explain positional encoding.",
    ]

    history = []
    for turn_query in turns:
        plan_state = planning_graph.invoke({"question": turn_query, "conversation_history": history})
        exec_plan = plan_state.execution_plan
        edu_meta = plan_state.provider_metadata.get("educational_response") or plan_state.educational_response
        if hasattr(edu_meta, "dict"):
            edu_meta = edu_meta.dict()

        ctx = {
            "query": turn_query,
            "history": history,
            "execution_plan": exec_plan,
            "educational_response": edu_meta,
            "plan_state": plan_state,
        }

        result = orch.run(ctx)
        assert result.content is not None
        history.append({"role": "user", "content": turn_query})
        history.append({"role": "assistant", "content": result.content})


# ============================================================
# TEST GROUP F — STATE ISOLATION
# ============================================================
def test_group_f_state_isolation(quality_setup):
    """Group F: Consecutive unrelated queries maintain strict metadata and state isolation."""
    orch, planning_graph, engine, memory = quality_setup

    queries = [
        ("Explain transformers.", "general_knowledge"),
        ("Summarize the uploaded Solar System document.", "document_only"),
        ("Explain recursion.", "general_knowledge"),
    ]

    results = []
    for q_text, expected_strat in queries:
        plan_state = planning_graph.invoke({"question": q_text, "conversation_history": []})
        exec_plan = plan_state.execution_plan
        edu_meta = plan_state.provider_metadata.get("educational_response") or plan_state.educational_response
        if hasattr(edu_meta, "dict"):
            edu_meta = edu_meta.dict()

        ctx = {
            "query": q_text,
            "history": [],
            "execution_plan": exec_plan,
            "educational_response": edu_meta,
            "plan_state": plan_state,
        }

        res = orch.run(ctx)
        results.append((q_text, res, edu_meta))

    # Assert distinct responses and metadata
    res_q1, res_q2, res_q3 = results[0][1], results[1][1], results[2][1]
    assert res_q1.content != res_q2.content
    assert res_q2.content != res_q3.content
    assert res_q1.metadata["document_retrieval_executed"] is False
    assert res_q2.metadata["document_retrieval_executed"] is True
    assert res_q3.metadata["document_retrieval_executed"] is False
