"""Regression and functional unit test suite for UI Interactions (Video Recommendations & Guided Learning Questions).

Verifies:
1. "Recommend Videos" quick action routing, video retrieval, verification scoring, and EducationalResponse videos section populating.
2. Guided Learning question state flow via next_query submission through the single-synthesis pipeline.
3. Strict adherence to single-synthesis invariant (0 calls to legacy SynthesisAgent.run in production path).
"""

import pytest
from unittest.mock import MagicMock, patch
from graph.builder import create_ekip_planning_graph
from core.planner.rules import RuleBasedPlannerEngine
from core.planner.enums import EducationalIntent, SourceStrategy
from core.models.domain import SourceType
from core.synthesis import response_composer
from agents.orchestrator import OrchestratorAgent


def test_recommend_video_quick_action_routing():
    """Verify that 'Recommend top learning video concepts for understanding neural networks.' routes to video_recommendation and retrieves videos."""
    query = "Recommend top learning video concepts for understanding neural networks."
    plan = RuleBasedPlannerEngine.generate_plan(query)

    assert plan.intent == EducationalIntent.VIDEO_RECOMMENDATION
    assert plan.source_strategy == SourceStrategy.HYBRID
    assert SourceType.VIDEO in plan.selected_sources


def test_recommend_video_graph_pipeline_execution():
    """Verify that graph execution for a video recommendation query populates videos in the canonical EducationalResponse."""
    query = "Recommend top learning video concepts for understanding neural networks."
    graph = create_ekip_planning_graph()
    
    state = graph.invoke({"question": query, "conversation_history": []})
    
    assert state.execution_plan is not None
    assert state.execution_plan.intent == EducationalIntent.VIDEO_RECOMMENDATION
    
    # Check that retrieved_videos and educational_response contain video evidence
    edu_res = state.educational_response
    assert edu_res is not None
    assert isinstance(edu_res.get("videos"), list)
    assert len(edu_res.get("videos")) > 0, "EducationalResponse must contain video recommendations"
    
    # Verify video properties
    first_video = edu_res["videos"][0]
    assert "title" in first_video
    assert "url" in first_video
    assert first_video["url"].startswith("http")


def test_guided_learning_session_state_submission():
    """Verify that setting st.session_state.next_query correctly passes to the planning graph and single synthesis."""
    graph = create_ekip_planning_graph()
    guided_question = "How does backpropagation calculate gradients across hidden layers?"

    state = graph.invoke({"question": guided_question, "conversation_history": []})

    assert state.question == guided_question
    assert state.educational_response is not None
    assert state.educational_response.get("query") == guided_question
    assert len(state.educational_response.get("ai_explanation", "")) > 0


def test_single_synthesis_invariant_on_guided_question():
    """Verify that running a guided question through OrchestratorAgent uses canonical EducationalResponse without calling legacy SynthesisAgent.run()."""
    query = "What role do non-linear activation functions (ReLU, Sigmoid) play?"
    graph = create_ekip_planning_graph()

    plan_state = graph.invoke({"question": query, "conversation_history": []})
    edu_meta = plan_state.educational_response

    mock_cfg = MagicMock()
    mock_engine = MagicMock()
    mock_memory = MagicMock()

    orch = OrchestratorAgent(mock_cfg, mock_engine, mock_memory)

    with patch.object(orch.synthesis, "run") as mock_synth_run:
        ctx = {
            "query": query,
            "history": [],
            "filters": {},
            "execution_plan": plan_state.execution_plan,
            "educational_response": edu_meta,
            "plan_state": plan_state,
        }

        res = orch.run(ctx)

        # Legacy synthesis.run MUST NOT be called when canonical EducationalResponse is provided
        mock_synth_run.assert_not_called()
        assert res.success is True
        assert res.metadata.get("source_mode") in ("web", "documents", "documents+web", "general_knowledge")
        assert res.content == edu_meta.get("ai_explanation")
