"""Automated Regression Suite for EKIP Single Synthesis Architecture Verification."""

import pytest
from unittest.mock import MagicMock, patch
from config import Config
from agents.orchestrator import OrchestratorAgent
from agents.base import AgentResult
from graph.builder import create_ekip_planning_graph


class DummyEngine:
    def __init__(self, has_docs=True):
        self.has_docs = has_docs
        self.doc_count = 5 if has_docs else 0
        self.cfg = type("Cfg", (), {"RERANK_TOP_K": 5})()

    def list_docs(self):
        return {"solar_system.pdf": {"chunks": 5, "pages": 2}} if self.has_docs else {}

    def dense_search(self, query, k=8, **kwargs):
        return []

    def sparse_search(self, query, k=8, **kwargs):
        return []

    def reciprocal_rank_fusion(self, dense, sparse):
        return []

    def rerank(self, query, fused, top_k=5):
        return []

    def compress_context(self, reranked, max_chunks=6):
        return []


class DummyMemory:
    def record_query_metrics(self, **kwargs):
        pass


def test_production_context_with_educational_response_skips_synthesis_agent():
    """TEST 1 & 2: Production context containing EducationalResponse skips SynthesisAgent.run and sets AgentResult.content."""
    engine = DummyEngine()
    memory = DummyMemory()
    orch = OrchestratorAgent(Config, engine, memory)

    # Mock SynthesisAgent.run to raise if called
    orch.synthesis.run = MagicMock(side_effect=AssertionError("SynthesisAgent.run MUST NOT be called when EducationalResponse exists!"))

    canonical_edu = {
        "ai_explanation": "This is the single canonical educational explanation.",
        "learning_summary": "Summary of canonical explanation.",
        "confidence": 0.95,
        "key_takeaways": ["Takeaway 1"],
    }

    context = {
        "query": "Explain quantum computing",
        "history": [],
        "educational_response": canonical_edu,
    }

    result = orch.run(context)

    # Assert SynthesisAgent.run was NEVER called
    orch.synthesis.run.assert_not_called()
    assert result.content == "This is the single canonical educational explanation."
    assert result.success is True


def test_general_knowledge_query_single_synthesis_pass():
    """TEST 3 & 5: General knowledge query through full graph + orchestrator flow produces consistent response and single synthesis."""
    graph = create_ekip_planning_graph()
    prompt = "Explain the core concepts of Transformer architectures in Machine Learning."
    plan_state = graph.invoke({"question": prompt, "conversation_history": []})

    edu_meta = plan_state.provider_metadata.get("educational_response") or plan_state.educational_response
    assert edu_meta is not None
    assert "ai_explanation" in edu_meta

    engine = DummyEngine(has_docs=False)
    memory = DummyMemory()
    orch = OrchestratorAgent(Config, engine, memory)

    # Spy on synthesis.run to verify it is NOT called during orch.run
    orch.synthesis.run = MagicMock()

    ctx = {
        "query": prompt,
        "history": [],
        "execution_plan": plan_state.execution_plan,
        "educational_response": edu_meta,
        "plan_state": plan_state,
    }

    result = orch.run(ctx)

    # SynthesisAgent.run should NOT be invoked
    orch.synthesis.run.assert_not_called()
    assert edu_meta["ai_explanation"] in result.content or result.content.strip() == edu_meta["ai_explanation"].strip()
    assert result.metadata["educational_response"] == edu_meta


def test_telemetry_consistency_for_general_knowledge():
    """TEST 7: Verify telemetry and metadata consistency for general knowledge queries."""
    graph = create_ekip_planning_graph()
    prompt = "Explain the core concepts of Transformer architectures in Machine Learning."
    plan_state = graph.invoke({"question": prompt, "conversation_history": []})
    edu_meta = plan_state.provider_metadata.get("educational_response") or plan_state.educational_response

    engine = DummyEngine(has_docs=True)
    memory = DummyMemory()
    orch = OrchestratorAgent(Config, engine, memory)

    ctx = {
        "query": prompt,
        "history": [],
        "execution_plan": plan_state.execution_plan,
        "educational_response": edu_meta,
        "plan_state": plan_state,
    }

    result = orch.run(ctx)
    meta = result.metadata

    assert meta["planner_source_strategy"] == "general_knowledge"
    assert meta["runtime_source_strategy"] == "general_knowledge"
    assert meta["document_retrieval_executed"] is False
    assert meta["retrieved_chunks_count"] == 0
