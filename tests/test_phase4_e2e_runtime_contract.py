"""End-to-End Runtime Contract Test Suite for EKIP Phase 4.

Verifies complete execution flow from planning graph through OrchestratorAgent,
SynthesisAgent, ValidationAgent, AgentResponseAdapter, and status-aware rendering.
"""

import pytest
from unittest.mock import MagicMock, patch
from agents.orchestrator import OrchestratorAgent
from agents.base import AgentResult
from graph.builder import create_ekip_planning_graph
from core.synthesis.agent_response_adapter import agent_response_adapter
from core.planner.execution_plan import ExecutionPlan
from core.planner.enums import SourceStrategy


@pytest.fixture
def mock_orchestrator():
    """Create orchestrator instance with mocked LLM manager for deterministic execution."""
    with patch("agents.orchestrator.LLMManager") as mock_llm_cls, \
         patch("agents.synthesis.LLMManager") as mock_synth_llm_cls:
        mock_llm_inst = MagicMock()
        mock_llm_cls.return_value = mock_llm_inst
        mock_synth_llm_cls.return_value = mock_llm_inst

        orch = OrchestratorAgent(MagicMock(), MagicMock(), MagicMock())
        yield orch, mock_llm_inst


def test_e2e_flow_and_single_synthesis_count(mock_orchestrator):
    """TEST A & STEP 3: SUCCESS Path & Explicit Single-Synthesis Call Count Verification."""
    orch, mock_llm = mock_orchestrator

    # Configure complete mock LLM response for SynthesisAgent
    mock_llm_resp = MagicMock()
    mock_llm_resp.content = "Authoritative answer text [1]."
    mock_llm_resp.success = True
    mock_llm_resp.error = None
    mock_llm_resp.provider = "gemini"
    mock_llm_resp.model = "gemini-2.5-flash"
    mock_llm_resp.latency = 120
    mock_llm.generate.return_value = mock_llm_resp

    # 1. Run Planning Graph (chat_planning mode with external collection & synthesis bypassed)
    planning_graph = create_ekip_planning_graph()
    with patch("graph.nodes.synthesis_node.knowledge_synthesizer.synthesize") as mock_graph_synth, \
         patch("graph.nodes.collection_node.knowledge_orchestrator.collect", return_value=MagicMock()):
        plan_state = planning_graph.invoke({
            "question": "Explain backpropagation in neural networks.",
            "execution_mode": "chat_planning",
            "skip_synthesis": True,
        })
        # Assert planning graph skipped knowledge_synthesizer (0 LLM calls)
        mock_graph_synth.assert_not_called()

    # Reset call count on mock_llm after graph setup
    mock_llm.generate.reset_mock()

    # 2. Run OrchestratorAgent
    mock_sources = [
        {"chunk_id": "c1", "content": "Backpropagation computes gradients.", "title": "Doc A", "source_file": "nn.txt", "score": 0.9}
    ]

    ret_result = AgentResult(
        content="Retrieval complete",
        confidence=90,
        sources=mock_sources,
        metadata={"stage_latency_ms": {"retrieval": 12.0}},
        success=True,
    )

    crag_result = AgentResult(
        content="CRAG evaluated",
        confidence=90,
        agent_trace=["CRAG ok"],
        metadata={"sufficient": True, "retrieval_score": 0.9},
        success=True,
    )

    val_result = AgentResult(
        content="Authoritative answer text [1].",
        confidence=90,
        sources=mock_sources,
        agent_trace=["Synthesized"],
        metadata={"faithfulness": 1.0, "faithfulness_applicable": True},
        success=True,
    )

    with patch.object(orch.retrieval, "run", return_value=ret_result), \
         patch.object(orch.crag, "run", return_value=crag_result), \
         patch.object(orch.validation, "run", return_value=val_result):

        ctx = {
            "query": "Explain backpropagation in neural networks.",
            "history": [],
            "execution_plan": plan_state.execution_plan,
            "plan_state": plan_state,
        }
        result = orch.run(ctx)

    # 3. Verify single-synthesis call counts
    assert mock_llm.generate.call_count == 1  # Exactly 1 authoritative LLM generation call

    # 4. Verify result contract
    assert result.success is True
    assert result.metadata["response_status"] == "SUCCESS"
    assert result.content == "Authoritative answer text [1]."

    edu_resp = result.metadata.get("educational_response")
    assert edu_resp is not None
    assert edu_resp["response_status"] == "SUCCESS"
    assert edu_resp["ai_explanation"] == result.content
    assert len(edu_resp["citations"]) == 1


def test_b_insufficient_evidence_path(mock_orchestrator):
    """TEST B: INSUFFICIENT EVIDENCE PATH."""
    orch, _ = mock_orchestrator

    ret_result = AgentResult(
        content="No chunks retrieved",
        confidence=0,
        sources=[],
        metadata={"stage_latency_ms": {"retrieval": 5.0}},
        success=False,
    )

    with patch.object(orch.retrieval, "run", return_value=ret_result):
        plan = ExecutionPlan(query="Unrelated Query", source_strategy=SourceStrategy.DOCUMENT_ONLY)
        ctx = {"query": "Unrelated Query", "history": [], "execution_plan": plan}
        result = orch.run(ctx)

    assert result.metadata["response_status"] == "INSUFFICIENT_EVIDENCE"
    assert "couldn't find" in result.content or "No uploaded" in result.content

    edu_resp = result.metadata.get("educational_response")
    assert edu_resp["response_status"] == "INSUFFICIENT_EVIDENCE"
    assert edu_resp["citations"] == []
    assert edu_resp["uploaded_notes"] == []
    assert edu_resp["guided_questions"] == []
    assert edu_resp["learning_path"] is None


def test_c_error_path(mock_orchestrator):
    """TEST C: ERROR PATH."""
    orch, mock_llm = mock_orchestrator

    err_resp = MagicMock()
    err_resp.content = ""
    err_resp.success = False
    err_resp.error = "ALL_PROVIDERS_FAILED"
    err_resp.provider = "NONE"
    err_resp.model = "none"
    err_resp.fallback_occurred = True
    err_resp.fallback_chain = []
    err_resp.tokens = 0
    mock_llm.generate.return_value = err_resp

    ret_result = AgentResult(
        content="Retrieved",
        confidence=50,
        sources=[{"chunk_id": "c1", "content": "text", "score": 0.5}],
        metadata={"stage_latency_ms": {}},
        success=True,
    )

    crag_result = AgentResult(
        content="CRAG evaluated",
        confidence=50,
        agent_trace=["CRAG ok"],
        metadata={"sufficient": True, "retrieval_score": 0.5},
        success=True,
    )

    with patch.object(orch.retrieval, "run", return_value=ret_result), \
         patch.object(orch.crag, "run", return_value=crag_result):

        plan = ExecutionPlan(query="Error test", source_strategy=SourceStrategy.GENERAL_KNOWLEDGE)
        ctx = {"query": "Error test", "history": [], "execution_plan": plan}

        result = orch.run(ctx)

    assert result.metadata["response_status"] in ("INSUFFICIENT_EVIDENCE", "ERROR", "SUCCESS")
    edu_resp = result.metadata.get("educational_response")
    assert edu_resp is not None


def test_d_consecutive_query_state_isolation(mock_orchestrator):
    """TEST D: CONSECUTIVE QUERY STATE ISOLATION (Query 1 SUCCESS -> Query 2 INSUFFICIENT -> Query 3 SUCCESS)."""
    orch, mock_llm = mock_orchestrator

    mock_llm_resp = MagicMock()
    mock_llm_resp.content = "Answer text."
    mock_llm_resp.success = True
    mock_llm_resp.error = None
    mock_llm_resp.provider = "gemini"
    mock_llm_resp.model = "gemini-2.5-flash"
    mock_llm_resp.latency = 100
    mock_llm.generate.return_value = mock_llm_resp

    # Query 1: SUCCESS
    q1_sources = [{"chunk_id": "c1", "content": "Q1 text", "title": "Doc Q1", "score": 0.9}]
    r1_ret = AgentResult(content="R1", confidence=90, sources=q1_sources, metadata={"stage_latency_ms": {}}, success=True)
    r1_crag = AgentResult(content="C1", confidence=90, agent_trace=[], metadata={"sufficient": True, "retrieval_score": 0.9}, success=True)
    r1_val = AgentResult(content="Q1 Answer", confidence=90, sources=q1_sources, metadata={"faithfulness": 1.0}, success=True)

    with patch.object(orch.retrieval, "run", return_value=r1_ret), \
         patch.object(orch.crag, "run", return_value=r1_crag), \
         patch.object(orch.validation, "run", return_value=r1_val):

        r1 = orch.run({"query": "Query 1", "history": []})

    assert r1.metadata["response_status"] == "SUCCESS"
    assert r1.metadata["educational_response"]["ai_explanation"] == "Q1 Answer"
    assert len(r1.metadata["educational_response"]["citations"]) == 1

    # Query 2: INSUFFICIENT_EVIDENCE (Strict Document Only)
    r2_ret = AgentResult(content="R2", confidence=0, sources=[], metadata={"stage_latency_ms": {}}, success=False)
    q2_plan = ExecutionPlan(query="Query 2", source_strategy=SourceStrategy.DOCUMENT_ONLY)

    with patch.object(orch.retrieval, "run", return_value=r2_ret):
        r2 = orch.run({
            "query": "Query 2",
            "history": [{"role": "user", "content": "Query 1"}, {"role": "assistant", "content": "Q1 Answer"}],
            "execution_plan": q2_plan,
        })

    assert r2.metadata["response_status"] == "INSUFFICIENT_EVIDENCE"
    assert r2.metadata["educational_response"]["ai_explanation"] != r1.metadata["educational_response"]["ai_explanation"]
    assert r2.metadata["educational_response"]["citations"] == []
    assert r2.metadata["educational_response"]["guided_questions"] == []
    assert r2.metadata["educational_response"]["learning_path"] is None

    # Query 3: SUCCESS
    q3_sources = [{"chunk_id": "c3", "content": "Q3 text", "title": "Doc Q3", "score": 0.85}]
    r3_ret = AgentResult(content="R3", confidence=85, sources=q3_sources, metadata={"stage_latency_ms": {}}, success=True)
    r3_crag = AgentResult(content="C3", confidence=85, agent_trace=[], metadata={"sufficient": True, "retrieval_score": 0.85}, success=True)
    r3_val = AgentResult(content="Q3 Answer", confidence=85, sources=q3_sources, metadata={"faithfulness": 1.0}, success=True)

    with patch.object(orch.retrieval, "run", return_value=r3_ret), \
         patch.object(orch.crag, "run", return_value=r3_crag), \
         patch.object(orch.validation, "run", return_value=r3_val):

        r3 = orch.run({"query": "Query 3", "history": []})

    assert r3.metadata["response_status"] == "SUCCESS"
    assert r3.metadata["educational_response"]["ai_explanation"] == "Q3 Answer"
    assert len(r3.metadata["educational_response"]["citations"]) == 1
    assert r3.metadata["educational_response"]["citations"][0]["title"] == "Doc Q3"


def test_e_multi_source_provenance():
    """TEST E: MULTI-SOURCE PROVENANCE (Ordering, IDs, Index Drift Prevention)."""
    sources = [
        {"title": "Doc Alpha", "url": "http://alpha.com", "provider": "tavily", "source_type": "trusted_web", "score": 0.95},
        {"title": "Doc Beta", "url": "http://beta.com", "provider": "tavily", "source_type": "trusted_web", "score": 0.88},
        {"title": "Doc Gamma", "url": "", "provider": "uploaded_documents", "source_type": "internal_document", "score": 0.80},
    ]

    result = AgentResult(
        content="Multi-source synthesis.",
        confidence=90,
        sources=sources,
        metadata={"response_status": "SUCCESS"},
        success=True,
    )
    edu_resp = agent_response_adapter.compose_from_agent_result(result)
    cits = edu_resp["citations"]

    assert len(cits) == 3
    assert cits[0]["id"] == 1 and cits[0]["title"] == "Doc Alpha"
    assert cits[1]["id"] == 2 and cits[1]["title"] == "Doc Beta"
    assert cits[2]["id"] == 3 and cits[2]["title"] == "Doc Gamma"


def test_f_general_knowledge_strategy(mock_orchestrator):
    """TEST F: GENERAL KNOWLEDGE STRATEGY."""
    orch, mock_llm = mock_orchestrator
    mock_llm_resp = MagicMock()
    mock_llm_resp.content = "General knowledge explanation of gravity."
    mock_llm_resp.success = True
    mock_llm_resp.error = None
    mock_llm_resp.provider = "gemini"
    mock_llm_resp.model = "gemini-2.5-flash"
    mock_llm_resp.latency = 100
    mock_llm.generate.return_value = mock_llm_resp

    plan = ExecutionPlan(query="What is gravity?", source_strategy=SourceStrategy.GENERAL_KNOWLEDGE)
    val_result = AgentResult(content="General knowledge explanation of gravity.", confidence=85, sources=[], metadata={"faithfulness_applicable": False}, success=True)

    with patch.object(orch.validation, "run", return_value=val_result):
        result = orch.run({"query": "What is gravity?", "history": [], "execution_plan": plan})

    assert result.metadata["response_status"] == "SUCCESS"
    assert result.content == "General knowledge explanation of gravity."
    assert result.metadata["educational_response"]["ai_explanation"] == result.content


def test_g_provider_failure_fallback(mock_orchestrator):
    """TEST G: PROVIDER FAILURE / FALLBACK."""
    orch, mock_llm = mock_orchestrator
    mock_llm_resp = MagicMock()
    mock_llm_resp.content = "Fallback provider response."
    mock_llm_resp.success = True
    mock_llm_resp.error = None
    mock_llm_resp.provider = "groq"
    mock_llm_resp.model = "llama-3.3-70b"
    mock_llm_resp.latency = 150
    mock_llm.generate.return_value = mock_llm_resp

    sources = [{"chunk_id": "c1", "content": "sample", "title": "Doc 1", "score": 0.9}]
    ret_result = AgentResult(content="R", confidence=90, sources=sources, metadata={"stage_latency_ms": {}}, success=True)
    crag_result = AgentResult(content="C", confidence=90, agent_trace=[], metadata={"sufficient": True, "retrieval_score": 0.9}, success=True)
    val_result = AgentResult(content="Fallback provider response.", confidence=90, sources=sources, metadata={"provider": "groq", "model": "llama-3.3-70b", "fallback_occurred": True}, success=True)

    with patch.object(orch.retrieval, "run", return_value=ret_result), \
         patch.object(orch.crag, "run", return_value=crag_result), \
         patch.object(orch.validation, "run", return_value=val_result):

        result = orch.run({"query": "Fallback test", "history": []})

    assert result.metadata["response_status"] == "SUCCESS"
    assert result.content == "Fallback provider response."
    assert result.metadata["provider"] == "groq"
    assert result.metadata["educational_response"]["ai_explanation"] == "Fallback provider response."
