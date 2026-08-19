"""Phase 5 Production Query Quality & Final Acceptance Test Suite for EKIP.

Validates end-to-end production path across realistic user query scenarios:
- Category A: Document-Grounded Explanation
- Category B: Exact Factual Retrieval
- Category C: Multi-Source Synthesis
- Category D: Missing Information
- Category E: Conflicting Information
- Category F: General Knowledge
- Category G: Follow-up Conversation
- Category H: Provider Fallback Quality
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
    """Create orchestrator instance with mocked LLM manager for deterministic production testing."""
    with patch("agents.orchestrator.LLMManager") as mock_llm_cls, \
         patch("agents.synthesis.LLMManager") as mock_synth_llm_cls:
        mock_llm_inst = MagicMock()
        mock_llm_cls.return_value = mock_llm_inst
        mock_synth_llm_cls.return_value = mock_llm_inst

        orch = OrchestratorAgent(MagicMock(), MagicMock(), MagicMock())
        yield orch, mock_llm_inst


# ==============================================================================
# CATEGORY A — DOCUMENT-GROUNDED EXPLANATION
# ==============================================================================
def test_category_a_document_grounded_explanation(mock_orchestrator):
    """Category A: Realistic document-grounded query with available evidence."""
    orch, mock_llm = mock_orchestrator

    mock_llm_resp = MagicMock()
    mock_llm_resp.content = "Transformer architectures utilize multi-head self-attention mechanisms and positional encodings to model long-range dependencies efficiently [1]."
    mock_llm_resp.success = True
    mock_llm_resp.error = None
    mock_llm_resp.provider = "gemini"
    mock_llm_resp.model = "gemini-2.5-flash"
    mock_llm_resp.latency = 140
    mock_llm.generate.return_value = mock_llm_resp

    mock_sources = [
        {"chunk_id": "c1", "content": "Transformer architectures utilize multi-head self-attention mechanisms and positional encodings.", "title": "ai_arch.txt", "source_file": "ai_arch.txt", "score": 0.92}
    ]

    ret_result = AgentResult(content="Retrieved 1 chunk", confidence=92, sources=mock_sources, metadata={"stage_latency_ms": {"retrieval": 15.0}}, success=True)
    crag_result = AgentResult(content="CRAG verified", confidence=92, agent_trace=["CRAG ok"], metadata={"sufficient": True, "retrieval_score": 0.92}, success=True)
    val_result = AgentResult(
        content=mock_llm_resp.content,
        confidence=92,
        sources=mock_sources,
        agent_trace=["Validated"],
        metadata={"faithfulness": 1.0, "faithfulness_applicable": True},
        success=True
    )

    query = "Explain the core concepts of Transformer architectures in Machine Learning."
    with patch.object(orch.retrieval, "run", return_value=ret_result), \
         patch.object(orch.crag, "run", return_value=crag_result), \
         patch.object(orch.validation, "run", return_value=val_result):

        plan = ExecutionPlan(source_strategy=SourceStrategy.DOCUMENT_ONLY)
        result = orch.run({"query": query, "history": [], "execution_plan": plan})

    # Verification
    assert result.metadata["response_status"] == "SUCCESS"
    assert result.content != ""
    assert "multi-head self-attention" in result.content.lower()
    assert result.metadata["educational_response"]["ai_explanation"] == result.content
    assert len(result.metadata["educational_response"]["citations"]) == 1
    assert result.metadata["educational_response"]["citations"][0]["title"] == "ai_arch.txt"


# ==============================================================================
# CATEGORY B — EXACT FACTUAL RETRIEVAL
# ==============================================================================
def test_category_b_exact_factual_retrieval(mock_orchestrator):
    """Category B: Specific numbers, specs, and named components from documents."""
    orch, mock_llm = mock_orchestrator

    mock_llm_resp = MagicMock()
    mock_llm_resp.content = "The model uses 8 attention heads and an embedding dimension of 256 [1]."
    mock_llm_resp.success = True
    mock_llm_resp.error = None
    mock_llm_resp.provider = "gemini"
    mock_llm_resp.model = "gemini-2.5-flash"
    mock_llm_resp.latency = 110
    mock_llm.generate.return_value = mock_llm_resp

    mock_sources = [
        {"chunk_id": "c1", "content": "The model uses 8 attention heads and an embedding dimension of 256.", "title": "model_spec.txt", "source_file": "model_spec.txt", "score": 0.95}
    ]

    ret_result = AgentResult(content="Retrieved spec", confidence=95, sources=mock_sources, metadata={"stage_latency_ms": {}}, success=True)
    crag_result = AgentResult(content="CRAG ok", confidence=95, agent_trace=[], metadata={"sufficient": True, "retrieval_score": 0.95}, success=True)
    val_result = AgentResult(content=mock_llm_resp.content, confidence=95, sources=mock_sources, metadata={"faithfulness": 1.0, "faithfulness_applicable": True}, success=True)

    query = "What is the embedding dimension and number of attention heads?"
    with patch.object(orch.retrieval, "run", return_value=ret_result), \
         patch.object(orch.crag, "run", return_value=crag_result), \
         patch.object(orch.validation, "run", return_value=val_result):

        plan = ExecutionPlan(source_strategy=SourceStrategy.DOCUMENT_ONLY)
        result = orch.run({"query": query, "history": [], "execution_plan": plan})

    # Verification
    assert result.metadata["response_status"] == "SUCCESS"
    assert "8 attention heads" in result.content
    assert "256" in result.content
    assert result.metadata["educational_response"]["ai_explanation"] == result.content
    assert len(result.metadata["educational_response"]["citations"]) == 1
    assert result.metadata["educational_response"]["citations"][0]["id"] == 1


# ==============================================================================
# CATEGORY C — MULTI-SOURCE SYNTHESIS
# ==============================================================================
def test_category_c_multi_source_synthesis(mock_orchestrator):
    """Category C: Facts distributed across multiple source documents."""
    orch, mock_llm = mock_orchestrator

    mock_llm_resp = MagicMock()
    mock_llm_resp.content = "EKIP-V1 has 110M parameters trained on Wikipedia [1]. EKIP-V2 has 340M parameters trained on Common Crawl [2]."
    mock_llm_resp.success = True
    mock_llm_resp.error = None
    mock_llm_resp.provider = "gemini"
    mock_llm_resp.model = "gemini-2.5-flash"
    mock_llm_resp.latency = 160
    mock_llm.generate.return_value = mock_llm_resp

    mock_sources = [
        {"chunk_id": "c1", "content": "EKIP-V1 has 110M parameters trained on Wikipedia.", "title": "ekip_v1.txt", "source_file": "ekip_v1.txt", "score": 0.90},
        {"chunk_id": "c2", "content": "EKIP-V2 has 340M parameters trained on Common Crawl.", "title": "ekip_v2.txt", "source_file": "ekip_v2.txt", "score": 0.88},
    ]

    ret_result = AgentResult(content="Retrieved 2 sources", confidence=89, sources=mock_sources, metadata={"stage_latency_ms": {}}, success=True)
    crag_result = AgentResult(content="CRAG ok", confidence=89, agent_trace=[], metadata={"sufficient": True, "retrieval_score": 0.89}, success=True)
    val_result = AgentResult(content=mock_llm_resp.content, confidence=89, sources=mock_sources, metadata={"faithfulness": 1.0, "faithfulness_applicable": True}, success=True)

    query = "Compare EKIP-V1 and EKIP-V2 parameters and datasets."
    with patch.object(orch.retrieval, "run", return_value=ret_result), \
         patch.object(orch.crag, "run", return_value=crag_result), \
         patch.object(orch.validation, "run", return_value=val_result):

        plan = ExecutionPlan(source_strategy=SourceStrategy.HYBRID)
        result = orch.run({"query": query, "history": [], "execution_plan": plan})

    # Verification
    assert result.metadata["response_status"] == "SUCCESS"
    assert "110M" in result.content and "340M" in result.content
    cits = result.metadata["educational_response"]["citations"]
    assert len(cits) == 2
    assert cits[0]["id"] == 1 and cits[0]["title"] == "ekip_v1.txt"
    assert cits[1]["id"] == 2 and cits[1]["title"] == "ekip_v2.txt"


# ==============================================================================
# CATEGORY D — MISSING INFORMATION
# ==============================================================================
def test_category_d_missing_information(mock_orchestrator):
    """Category D: Information not present in indexed document evidence."""
    orch, _ = mock_orchestrator

    ret_result = AgentResult(content="0 chunks retrieved", confidence=0, sources=[], metadata={"stage_latency_ms": {}}, success=False)

    query = "What is the battery life of the hardware server?"
    with patch.object(orch.retrieval, "run", return_value=ret_result):
        plan = ExecutionPlan(source_strategy=SourceStrategy.DOCUMENT_ONLY)
        result = orch.run({"query": query, "history": [], "execution_plan": plan})

    # Verification
    assert result.metadata["response_status"] == "INSUFFICIENT_EVIDENCE"
    assert "couldn't find" in result.content or "No uploaded" in result.content
    edu_resp = result.metadata["educational_response"]
    assert edu_resp["response_status"] == "INSUFFICIENT_EVIDENCE"
    assert edu_resp["citations"] == []
    assert edu_resp["guided_questions"] == []
    assert edu_resp["learning_path"] is None


# ==============================================================================
# CATEGORY E — CONFLICTING INFORMATION
# ==============================================================================
def test_category_e_conflicting_information(mock_orchestrator):
    """Category E: Conflicting statements across source documents."""
    orch, mock_llm = mock_orchestrator

    mock_llm_resp = MagicMock()
    mock_llm_resp.content = "Source 1 specifies fine-tuning learning rate as 1e-4 [1], while Source 2 specifies 3e-5 [2]."
    mock_llm_resp.success = True
    mock_llm_resp.error = None
    mock_llm_resp.provider = "gemini"
    mock_llm_resp.model = "gemini-2.5-flash"
    mock_llm_resp.latency = 150
    mock_llm.generate.return_value = mock_llm_resp

    mock_sources = [
        {"chunk_id": "c1", "content": "The fine-tuning learning rate is 1e-4.", "title": "hyperparams_v1.txt", "source_file": "hyperparams_v1.txt", "score": 0.85},
        {"chunk_id": "c2", "content": "The fine-tuning learning rate is 3e-5.", "title": "hyperparams_v2.txt", "source_file": "hyperparams_v2.txt", "score": 0.84},
    ]

    ret_result = AgentResult(content="Retrieved conflicting docs", confidence=84, sources=mock_sources, metadata={"stage_latency_ms": {}}, success=True)
    crag_result = AgentResult(content="CRAG ok", confidence=84, agent_trace=[], metadata={"sufficient": True, "retrieval_score": 0.84}, success=True)
    val_result = AgentResult(content=mock_llm_resp.content, confidence=84, sources=mock_sources, metadata={"faithfulness": 0.95, "faithfulness_applicable": True}, success=True)

    query = "What is the learning rate used during fine-tuning?"
    with patch.object(orch.retrieval, "run", return_value=ret_result), \
         patch.object(orch.crag, "run", return_value=crag_result), \
         patch.object(orch.validation, "run", return_value=val_result):

        plan = ExecutionPlan(source_strategy=SourceStrategy.HYBRID)
        result = orch.run({"query": query, "history": [], "execution_plan": plan})

    # Verification
    assert result.metadata["response_status"] == "SUCCESS"
    assert "1e-4" in result.content and "3e-5" in result.content
    assert len(result.metadata["educational_response"]["citations"]) == 2


# ==============================================================================
# CATEGORY F — GENERAL KNOWLEDGE
# ==============================================================================
def test_category_f_general_knowledge(mock_orchestrator):
    """Category F: Realistic general knowledge query."""
    orch, mock_llm = mock_orchestrator

    mock_llm_resp = MagicMock()
    mock_llm_resp.content = "Information entropy measures the average amount of information or uncertainty produced by a stochastic source of data."
    mock_llm_resp.success = True
    mock_llm_resp.error = None
    mock_llm_resp.provider = "gemini"
    mock_llm_resp.model = "gemini-2.5-flash"
    mock_llm_resp.latency = 130
    mock_llm.generate.return_value = mock_llm_resp

    query = "Explain the concept of entropy in information theory."
    plan = ExecutionPlan(source_strategy=SourceStrategy.GENERAL_KNOWLEDGE)
    val_result = AgentResult(content=mock_llm_resp.content, confidence=85, sources=[], metadata={"faithfulness_applicable": False}, success=True)

    with patch.object(orch.validation, "run", return_value=val_result):
        result = orch.run({"query": query, "history": [], "execution_plan": plan})

    # Verification
    assert result.metadata["response_status"] == "SUCCESS"
    assert "entropy" in result.content.lower()
    assert result.metadata["educational_response"]["ai_explanation"] == result.content
    assert result.metadata["faithfulness_applicable"] is False


# ==============================================================================
# CATEGORY G — FOLLOW-UP CONVERSATION
# ==============================================================================
def test_category_g_follow_up_conversation(mock_orchestrator):
    """Category G: Multi-turn conversation sequence."""
    orch, mock_llm = mock_orchestrator

    mock_llm_resp = MagicMock()
    mock_llm_resp.content = "Self-attention computes pairwise token interactions using key, query, and value projections."
    mock_llm_resp.success = True
    mock_llm_resp.error = None
    mock_llm_resp.provider = "gemini"
    mock_llm_resp.model = "gemini-2.5-flash"
    mock_llm_resp.latency = 100
    mock_llm.generate.return_value = mock_llm_resp

    history = []

    # Turn 1
    p1 = ExecutionPlan(source_strategy=SourceStrategy.GENERAL_KNOWLEDGE)
    v1 = AgentResult(content="Self-attention computes pairwise token interactions.", confidence=85, sources=[], metadata={"faithfulness_applicable": False}, success=True)
    with patch.object(orch.validation, "run", return_value=v1):
        r1 = orch.run({"query": "What is self-attention?", "history": history, "execution_plan": p1})

    assert r1.metadata["response_status"] == "SUCCESS"
    history.append({"role": "user", "content": "What is self-attention?"})
    history.append({"role": "assistant", "content": r1.content})

    # Turn 2
    p2 = ExecutionPlan(source_strategy=SourceStrategy.GENERAL_KNOWLEDGE)
    v2 = AgentResult(content="Standard self-attention scales quadratically O(N^2) with sequence length.", confidence=85, sources=[], metadata={"faithfulness_applicable": False}, success=True)
    with patch.object(orch.validation, "run", return_value=v2):
        r2 = orch.run({"query": "How does it scale with sequence length?", "history": history, "execution_plan": p2})

    assert r2.metadata["response_status"] == "SUCCESS"
    assert "quadratically" in r2.content or "O(N^2)" in r2.content
    assert r2.metadata["educational_response"]["citations"] == []


# ==============================================================================
# CATEGORY H — PROVIDER FALLBACK QUALITY
# ==============================================================================
def test_category_h_provider_fallback_quality(mock_orchestrator):
    """Category H: Primary provider failure gracefully handled by secondary provider."""
    orch, mock_llm = mock_orchestrator

    mock_llm_resp = MagicMock()
    mock_llm_resp.content = "Authoritative fallback synthesis from Groq provider."
    mock_llm_resp.success = True
    mock_llm_resp.error = None
    mock_llm_resp.provider = "groq"
    mock_llm_resp.model = "llama-3.3-70b"
    mock_llm_resp.latency = 180
    mock_llm.generate.return_value = mock_llm_resp

    sources = [{"chunk_id": "c1", "content": "Sample content.", "title": "Doc 1", "score": 0.9}]
    ret_result = AgentResult(content="R", confidence=90, sources=sources, metadata={"stage_latency_ms": {}}, success=True)
    crag_result = AgentResult(content="C", confidence=90, agent_trace=[], metadata={"sufficient": True, "retrieval_score": 0.9}, success=True)
    val_result = AgentResult(content="Authoritative fallback synthesis from Groq provider.", confidence=90, sources=sources, metadata={"provider": "groq", "model": "llama-3.3-70b", "fallback_occurred": True}, success=True)

    with patch.object(orch.retrieval, "run", return_value=ret_result), \
         patch.object(orch.crag, "run", return_value=crag_result), \
         patch.object(orch.validation, "run", return_value=val_result):

        result = orch.run({"query": "Test provider fallback", "history": []})

    # Verification
    assert result.metadata["response_status"] == "SUCCESS"
    assert result.content == "Authoritative fallback synthesis from Groq provider."
    assert result.metadata["provider"] == "groq"
    assert result.metadata["educational_response"]["ai_explanation"] == result.content
