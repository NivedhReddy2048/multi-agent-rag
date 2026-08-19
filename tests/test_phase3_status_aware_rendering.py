"""Targeted Test Suite for Phase 3: Status-Aware UI Integration & Truthful Rendering."""

import pytest
from unittest.mock import MagicMock, patch
from agents.base import AgentResult
from core.synthesis.agent_response_adapter import agent_response_adapter


def test_1_success_rendering_contract():
    """Test 1: Verify SUCCESS status constructs authoritative educational payload matching AgentResult.content."""
    result = AgentResult(
        content="Primary authoritative AI explanation text.",
        confidence=92,
        sources=[{"title": "Doc A", "provider": "uploaded_documents", "source_type": "internal_document"}],
        metadata={"response_status": "SUCCESS"},
        success=True,
    )
    edu_resp = agent_response_adapter.compose_from_agent_result(result)

    assert edu_resp["response_status"] == "SUCCESS"
    assert edu_resp["ai_explanation"] == "Primary authoritative AI explanation text."
    assert edu_resp["confidence"] == 0.92
    assert len(edu_resp["citations"]) == 1


def test_2_insufficient_evidence_suppression():
    """Test 2: Verify INSUFFICIENT_EVIDENCE status suppresses educational scaffolding & fake categories."""
    insuff_msg = "I couldn't find relevant information in your indexed documents."
    result = AgentResult(
        content=insuff_msg,
        confidence=0,
        sources=[{"title": "Unmatched Chunk", "provider": "uploaded_documents"}],
        metadata={"response_status": "INSUFFICIENT_EVIDENCE", "failure_reason": "INSUFFICIENT_EVIDENCE"},
        success=False,
    )
    edu_resp = agent_response_adapter.compose_from_agent_result(result)

    assert edu_resp["response_status"] == "INSUFFICIENT_EVIDENCE"
    assert edu_resp["ai_explanation"] == insuff_msg
    assert len(edu_resp["citations"]) == 0
    assert len(edu_resp["uploaded_notes"]) == 0
    assert len(edu_resp["guided_questions"]) == 0
    assert edu_resp["learning_path"] is None
    assert edu_resp["key_takeaways"] == []


def test_3_error_suppression():
    """Test 3: Verify ERROR status suppresses educational scaffolding and presents clear error state."""
    err_msg = "Execution error occurred during pipeline processing."
    result = AgentResult(
        content=err_msg,
        confidence=0,
        sources=[],
        metadata={"response_status": "ERROR"},
        success=False,
        error="API Connection Failed",
    )
    edu_resp = agent_response_adapter.compose_from_agent_result(result)

    assert edu_resp["response_status"] == "ERROR"
    assert edu_resp["ai_explanation"] == err_msg
    assert len(edu_resp["citations"]) == 0
    assert edu_resp["learning_path"] is None


def test_4_no_stale_success_data():
    """Test 4: Verify Request 2 (INSUFFICIENT_EVIDENCE) does not inherit Request 1's (SUCCESS) educational content."""
    # Request 1: SUCCESS
    req1_result = AgentResult(
        content="Request 1 answer.",
        confidence=90,
        sources=[{"title": "Req1 Doc", "provider": "uploaded_documents", "source_type": "internal_document"}],
        metadata={"response_status": "SUCCESS", "key_takeaways": ["Req 1 Takeaway"]},
        success=True,
    )
    req1_edu = agent_response_adapter.compose_from_agent_result(req1_result)
    assert req1_edu["response_status"] == "SUCCESS"
    assert len(req1_edu["citations"]) == 1

    # Request 2: INSUFFICIENT_EVIDENCE
    req2_result = AgentResult(
        content="I couldn't find information for Request 2.",
        confidence=0,
        sources=[],
        metadata={"response_status": "INSUFFICIENT_EVIDENCE"},
        success=False,
    )
    req2_edu = agent_response_adapter.compose_from_agent_result(req2_result)

    assert req2_edu["response_status"] == "INSUFFICIENT_EVIDENCE"
    assert req2_edu["ai_explanation"] != req1_edu["ai_explanation"]
    assert req2_edu["citations"] == []
    assert req2_edu["key_takeaways"] == []
    assert req2_edu["learning_path"] is None


def test_5_empty_section_suppression():
    """Test 5: Verify empty educational sections are not populated with fake items for SUCCESS."""
    result = AgentResult(
        content="General answer without extra media.",
        confidence=85,
        sources=[],
        metadata={"response_status": "SUCCESS", "key_takeaways": []},
        success=True,
    )
    edu_resp = agent_response_adapter.compose_from_agent_result(result)

    assert edu_resp["videos"] == []
    assert edu_resp["books"] == []
    assert edu_resp["research"] == []
    assert edu_resp["key_takeaways"] == []
    assert edu_resp["conflicts"] == []


def test_6_confidence_normalization():
    """Test 6: Verify confidence values 85 -> 0.85, 0.85 -> 0.85, 100 -> 1.0, 0 -> 0.0 without double-normalizing."""
    r_85 = AgentResult(content="c", confidence=85, metadata={"response_status": "SUCCESS"})
    r_float = AgentResult(content="c", confidence=0.85, metadata={"response_status": "SUCCESS"})
    r_100 = AgentResult(content="c", confidence=100, metadata={"response_status": "SUCCESS"})
    r_0 = AgentResult(content="c", confidence=0, metadata={"response_status": "SUCCESS"})

    assert agent_response_adapter.compose_from_agent_result(r_85)["confidence"] == 0.85
    assert agent_response_adapter.compose_from_agent_result(r_float)["confidence"] == 0.85
    assert agent_response_adapter.compose_from_agent_result(r_100)["confidence"] == 1.0
    assert agent_response_adapter.compose_from_agent_result(r_0)["confidence"] == 0.0


def test_7_faithfulness_is_not_agreement():
    """Test 7: Verify faithfulness is explicitly tracked and not blindly copied into agreement if agreement is unavailable."""
    result = AgentResult(
        content="Validated content",
        confidence=80,
        sources=[],
        metadata={
            "response_status": "SUCCESS",
            "faithfulness": 0.95,
            "faithfulness_applicable": True,
            "faithfulness_reason": "claim_level_citation_verification",
            # agreement is NOT present in metadata
        },
        success=True,
    )
    edu_resp = agent_response_adapter.compose_from_agent_result(result)

    assert edu_resp["synthesis_metadata"]["faithfulness"] == 0.95
    assert edu_resp["synthesis_metadata"]["faithfulness_applicable"] is True
    assert edu_resp["agreement"] == 0.0


def test_8_legacy_full_mode_preservation():
    """Test 8: Verify legacy execution_mode="full" still works as intended in graph nodes."""
    from graph.nodes.synthesis_node import knowledge_synthesis_node
    from graph.state import EKIPGraphState

    state = EKIPGraphState(
        question="What is deep learning?",
        execution_mode="full",
        skip_synthesis=False,
        provider_metadata={
            "verified_collection": {
                "query": "What is deep learning?",
                "verified_results": [],
                "overall_confidence": 0.9,
                "overall_agreement": 0.9,
                "verification_summary": "Verified",
            }
        }
    )

    with patch("core.synthesis.knowledge_synthesizer.synthesize") as mock_synth, \
         patch("core.synthesis.response_composer.compose_response") as mock_comp:

        mock_synth.return_value = MagicMock()
        mock_comp_resp = MagicMock()
        mock_comp_resp.dict.return_value = {"ai_explanation": "Legacy synthesis response"}
        mock_comp.return_value = mock_comp_resp

        updated_state = knowledge_synthesis_node(state)
        mock_synth.assert_called_once()
        mock_comp.assert_called_once()
        assert updated_state.educational_response == {"ai_explanation": "Legacy synthesis response"}
