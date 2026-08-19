import pytest
from unittest.mock import MagicMock, patch
from agents.orchestrator import OrchestratorAgent
from agents.validation import ValidationAgent
from agents.synthesis import SynthesisAgent
from core.synthesis.prompt_builder import EducationalPromptBuilder
from core.models.verification import VerifiedKnowledgeCollection, VerifiedKnowledgeResult
from core.planner.enums import SourceStrategy, EducationalIntent
from core.planner.execution_plan import ExecutionPlan
from agents.base import AgentResult

def test_1_fallback_no_type_error():
    """Verify primary fallback in OrchestratorAgent does not raise TypeError: system_prompt."""
    mock_cfg = MagicMock()
    mock_engine = MagicMock()
    mock_memory = MagicMock()
    mock_llm = MagicMock()
    
    # Simulate primary synthesis returning empty output
    mock_synth_res = AgentResult(content="", success=False, metadata={"error": "empty"})
    mock_fallback_resp = MagicMock(content="Fallback educational content")
    mock_llm.generate.return_value = mock_fallback_resp

    orchestrator = OrchestratorAgent(config=mock_cfg, engine=mock_engine, memory=mock_memory)
    orchestrator.llm_manager = mock_llm

    with patch.object(orchestrator, "_synthesize", return_value=mock_synth_res):
        context = {
            "query": "What is attention?",
            "request_id": "test_fb",
        }
        res = orchestrator.run(context)
        assert res.content == "Fallback educational content"
        # Ensure generate was called without system_prompt kwarg
        assert mock_llm.generate.called
        kwargs = mock_llm.generate.call_args.kwargs
        assert "system_prompt" not in kwargs

def test_2_general_knowledge_faithfulness_not_applicable():
    """Verify GENERAL_KNOWLEDGE responses return faithfulness = None and applicable = False."""
    val_agent = ValidationAgent()
    context = {
        "answer": "Transformers use self-attention to model long-range context.",
        "sources": [],
        "query": "Explain Transformers",
        "source_mode": "general_knowledge",
        "source_strategy": "general_knowledge",
    }
    res = val_agent.run(context)
    assert res.metadata["faithfulness"] is None
    assert res.metadata["faithfulness_applicable"] is False
    assert res.metadata["faithfulness_reason"] == "general_knowledge_no_document_grounding_required"
    assert "CITATIONS_NOT_DETECTED" not in res.metadata["warnings"]

def test_3_document_only_supported_grounding():
    """Verify DOCUMENT_ONLY with supported evidence returns numeric faithfulness."""
    val_agent = ValidationAgent()
    context = {
        "answer": "EKIP-MiniTransformer uses 8 attention heads.",
        "sources": [{"content": "EKIP-MiniTransformer uses 8 attention heads in total.", "source_file": "doc_a.txt"}],
        "query": "How many heads?",
        "source_mode": "documents",
        "source_strategy": "document_only",
    }
    res = val_agent.run(context)
    assert res.metadata["faithfulness"] == 1.0
    assert res.metadata["faithfulness_applicable"] is True

def test_4_and_5_missing_information_reporting():
    """Verify sentence acknowledging missing document information counts as grounded."""
    val_agent = ValidationAgent()
    context = {
        "answer": "EKIP-Encoder uses 6 blocks. ### ⚠️ Unsupported Information / Missing from Document\nThe provided document does not contain information about the decoder module.",
        "sources": [{"content": "EKIP-Encoder consists of 6 encoder blocks.", "source_file": "doc_b.txt"}],
        "query": "Explain encoder and decoder",
        "source_mode": "documents",
        "source_strategy": "document_only",
    }
    res = val_agent.run(context)
    assert res.metadata["faithfulness"] >= 0.80

def test_6_empty_retrieval_strict_insufficiency():
    """Verify empty retrieval in strict document mode sets faithfulness = 0.0 with reason."""
    val_agent = ValidationAgent()
    context = {
        "answer": "I couldn't find enough information in your indexed documents.",
        "sources": [],
        "query": "Explain quantum computing in my doc",
        "source_mode": "none",
        "source_strategy": "document_only",
    }
    res = val_agent.run(context)
    assert res.metadata["faithfulness"] == 0.0
    assert res.metadata["faithfulness_applicable"] is True
    assert res.metadata["faithfulness_reason"] == "empty_retrieval_insufficient_evidence"

def test_7_provenance_preservation():
    """Verify provenance metadata (page_number, chunk_id, score) survives synthesis into VerifiedKnowledgeResult."""
    builder = EducationalPromptBuilder()
    doc_result = VerifiedKnowledgeResult(
        title="doc_a.txt",
        content="Transformer specification text.",
        verification_score=0.88,
        provider="uploaded_documents",
        metadata={"page_number": 3, "chunk_id": "chunk_a_123"}
    )
    coll = VerifiedKnowledgeCollection(verified_results=[doc_result])
    prompt = builder.build_synthesis_prompt(query="Explain specs", verified_collection=coll)
    assert "Page: 3" in prompt
    assert "Chunk: chunk_a_123" in prompt

def test_8_conflicting_evidence_detection():
    """Verify conflict detection flags numeric discrepancy across sources."""
    mock_cfg = MagicMock()
    mock_cfg.MIN_RERANK_SCORE_STRICT = -1.0
    mock_cfg.MIN_RERANK_SCORE = 0.0
    mock_cfg.MAX_EVIDENCE_CHUNKS = 4
    mock_cfg.MAX_EVIDENCE_CHARS = 3000
    synth_agent = SynthesisAgent(config=mock_cfg)
    docs = [
        {"source_file": "doc_conf_a.txt", "content": "EKIP-Alpha uses 8 attention heads.", "score": 0.9},
        {"source_file": "doc_conf_b.txt", "content": "EKIP-Alpha uses 12 attention heads.", "score": 0.85},
    ]
    ctx = {"query": "How many heads?", "documents": docs, "source_strategy": "document_only"}
    prompt, inputs, intent, budgeted_docs, query, source_mode, template_name, system_msg, telemetry = synth_agent._prepare_prompt_and_context(ctx)
    assert "⚠️ DETECTED CONFLICTS IN EVIDENCE:" in system_msg
    assert "doc_conf_a.txt vs doc_conf_b.txt" in system_msg



def test_9_citation_anchoring_warning():
    """Verify CITATIONS_NOT_DETECTED warning is attached when document sources exist but no citations are in answer."""
    val_agent = ValidationAgent()
    context = {
        "answer": "EKIP model is an encoder-decoder network.",
        "sources": [{"content": "EKIP model is an encoder-decoder network.", "source_file": "doc_a.txt"}],
        "query": "What is EKIP model?",
        "source_mode": "documents",
        "source_strategy": "document_only",
    }
    res = val_agent.run(context)
    assert "CITATIONS_NOT_DETECTED" in res.metadata["warnings"]

def test_10_general_knowledge_unaffected():
    """Verify general knowledge mode is not burdened by document citation requirements."""
    builder = EducationalPromptBuilder()
    coll = VerifiedKnowledgeCollection()
    plan = ExecutionPlan(source_strategy=SourceStrategy.GENERAL_KNOWLEDGE)
    prompt = builder.build_synthesis_prompt(query="Explain neural networks", verified_collection=coll, plan=plan)
    assert "NORMAL EDUCATIONAL MODE" in prompt or "Source Strategy: general_knowledge" in prompt

def test_11_agent_result_backward_compatibility():
    """Verify AgentResult contract remains compatible with all downstream consumers."""
    res = AgentResult(
        content="Test content",
        confidence=90,
        sources=[{"source_file": "doc.txt", "chunk_id": "c1", "page_number": 1}],
        metadata={"faithfulness": 0.95, "faithfulness_applicable": True}
    )
    assert res.content == "Test content"
    assert res.confidence == 90
    assert len(res.sources) == 1
    assert res.metadata["faithfulness"] == 0.95

def test_12_timeout_behavior_preserved():
    """Verify timeout configuration settings are present in Config."""
    from config.settings import Config
    cfg = Config()
    assert hasattr(cfg, "LLM_MAX_WAIT_SECONDS")
    assert hasattr(cfg, "LLM_TIMEOUT_SECONDS")
