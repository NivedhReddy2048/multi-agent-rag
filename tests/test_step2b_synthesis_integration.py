"""Targeted Test Suite for Step 2B — Educational Prompt Builder Integration & Synthesis Agent."""

import pytest
from unittest.mock import MagicMock, patch
from agents.synthesis import SynthesisAgent
from agents.orchestrator import OrchestratorAgent
from core.planner.enums import SourceStrategy
from core.planner.execution_plan import ExecutionPlan
from config.settings import Config


def test_1_general_educational_query_uses_educational_prompt_builder_and_configured_timeout():
    """TEST 1: General educational query uses GENERAL_KNOWLEDGE path, EducationalPromptBuilder, and configured timeout."""
    agent = SynthesisAgent(Config)

    synth_ctx = {
        "query": "Explain the core concepts of Transformer architectures in Machine Learning.",
        "documents": [],
        "history": [],
        "intent": "QA",
        "source_mode": "general_knowledge",
        "source_strategy": "general_knowledge",
        "request_id": "test_req_1",
    }

    with patch.object(agent.llm_manager, "generate") as mock_generate:
        mock_generate.return_value = MagicMock(
            provider="gemini",
            model="gemini-2.5-flash",
            content="Transformers solve sequential constraints of RNNs using self-attention...",
            latency=120.0,
            tokens=150,
            success=True,
            error="",
            fallback_occurred=False,
            fallback_chain=[],
        )

        res = agent.run(synth_ctx)

        assert res.success is True
        assert "Transformers solve" in res.content
        mock_generate.assert_called_once()
        
        # Verify passed arguments to LLMManager.generate
        call_kwargs = mock_generate.call_args.kwargs
        assert call_kwargs["timeout"] >= 15.0, f"Expected timeout >= 15.0, got: {call_kwargs['timeout']}"

        # Verify Master Educational Framework is present in system prompt
        prompt_arg = mock_generate.call_args.args[0]
        inputs_arg = mock_generate.call_args.args[1]
        formatted_prompt = prompt_arg.format(**inputs_arg)

        assert "PEDAGOGICAL & EXPLANATION FRAMEWORK:" in formatted_prompt
        assert 'Problem & Motivation ("Why before How")' in formatted_prompt
        assert "Core Intuition" in formatted_prompt
        assert "Major Components & Architecture" in formatted_prompt


def test_2_general_educational_query_no_evidence_permits_core_knowledge():
    """TEST 2: General educational query with no evidence permits core model knowledge explanation without refusal."""
    agent = SynthesisAgent(Config)

    synth_ctx = {
        "query": "What is backpropagation in deep learning?",
        "documents": [],
        "history": [],
        "intent": "QA",
        "source_mode": "general_knowledge",
        "source_strategy": "general_knowledge",
        "request_id": "test_req_2",
    }

    with patch.object(agent.llm_manager, "generate") as mock_generate:
        mock_generate.return_value = MagicMock(
            provider="gemini",
            model="gemini-2.5-flash",
            content="Backpropagation is an optimization technique...",
            latency=100.0,
            tokens=100,
            success=True,
            error="",
            fallback_occurred=False,
            fallback_chain=[],
        )

        res = agent.run(synth_ctx)
        formatted_prompt = mock_generate.call_args.args[0].format(**mock_generate.call_args.args[1])

        assert "DO NOT allow it to block or distort your answer" in formatted_prompt
        assert "Use general model knowledge" in formatted_prompt
        assert "do NOT output a refusal statement" in formatted_prompt


def test_3_strict_document_query_preserves_strict_mode():
    """TEST 3: Explicit strict document query preserves EXPLICIT STRICT DOCUMENT MODE."""
    agent = SynthesisAgent(Config)

    query = "Using only my uploaded document, explain Transformer architecture."
    synth_ctx = {
        "query": query,
        "documents": [],
        "history": [],
        "intent": "QA",
        "source_mode": "documents",
        "source_strategy": "document_only",
        "request_id": "test_req_3",
    }

    with patch.object(agent.llm_manager, "generate") as mock_generate:
        mock_generate.return_value = MagicMock(
            provider="uploaded_documents",
            model="gemini-2.5-flash",
            content="I couldn't find relevant information about your query in your uploaded document.",
            latency=80.0,
            tokens=50,
            success=True,
            error="",
            fallback_occurred=False,
            fallback_chain=[],
        )

        res = agent.run(synth_ctx)
        formatted_prompt = mock_generate.call_args.args[0].format(**mock_generate.call_args.args[1])

        assert "EXPLICIT STRICT DOCUMENT MODE" in formatted_prompt
        assert "Base your explanation strictly on the VERIFIED KNOWLEDGE EVIDENCE" in formatted_prompt


def test_4_configured_timeout_propagation():
    """TEST 4: Configured LLM_MAX_WAIT_SECONDS is passed to LLMManager.generate rather than overriding with 2.0s."""
    class CustomConfig:
        LLM_MAX_WAIT_SECONDS = 25.0

    agent = SynthesisAgent(CustomConfig)

    synth_ctx = {
        "query": "Explain Machine Learning.",
        "documents": [],
        "history": [],
        "intent": "QA",
        "source_mode": "general_knowledge",
        "source_strategy": "general_knowledge",
        "request_id": "test_req_4",
    }

    with patch.object(agent.llm_manager, "generate") as mock_generate:
        mock_generate.return_value = MagicMock(
            provider="gemini",
            model="gemini-2.5-flash",
            content="Machine learning is...",
            latency=50.0,
            tokens=30,
            success=True,
            error="",
            fallback_occurred=False,
            fallback_chain=[],
        )

        agent.run(synth_ctx)
        call_kwargs = mock_generate.call_args.kwargs
        assert call_kwargs["timeout"] == 25.0, f"Expected timeout=25.0, got: {call_kwargs['timeout']}"


def test_5_agent_result_backward_compatibility():
    """TEST 5: SynthesisAgent output contract remains fully compatible with OrchestratorAgent and ValidationAgent."""
    agent = SynthesisAgent(Config)

    synth_ctx = {
        "query": "Explain Python lists.",
        "documents": [],
        "history": [],
        "intent": "QA",
        "source_mode": "general_knowledge",
        "source_strategy": "general_knowledge",
        "request_id": "test_req_5",
    }

    with patch.object(agent.llm_manager, "generate") as mock_generate:
        mock_generate.return_value = MagicMock(
            provider="gemini",
            model="gemini-2.5-flash",
            content="Python lists are ordered, mutable sequences...",
            latency=90.0,
            tokens=80,
            success=True,
            error="",
            fallback_occurred=False,
            fallback_chain=[],
        )

        res = agent.run(synth_ctx)

        assert hasattr(res, "content")
        assert hasattr(res, "confidence")
        assert hasattr(res, "sources")
        assert hasattr(res, "agent_trace")
        assert hasattr(res, "metadata")
        assert hasattr(res, "success")
        assert isinstance(res.metadata, dict)
        assert res.metadata["provider"] == "gemini"
        assert res.metadata["model"] == "gemini-2.5-flash"
