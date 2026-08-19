"""LangGraph Guided Learning Node for EKIP Educational Workflow."""

from graph.state import EKIPGraphState
from core.models.synthesis import EducationalResponse
from core.synthesis import guided_learning_engine
from core.logger import get_logger

logger = get_logger("graph.nodes.guided_learning")


def guided_learning_node(state: EKIPGraphState) -> EKIPGraphState:
    """Generates context-aware follow-up questions and topic progression learning path."""
    edu_dict = state.provider_metadata.get("educational_response") or state.educational_response

    try:
        from core.synthesis.guided_learning import extract_canonical_topic
        canonical_topic = extract_canonical_topic(state.question, plan=state.execution_plan)

        guided_qs = guided_learning_engine.generate_guided_questions(
            state.question,
            topic=canonical_topic,
            plan=state.execution_plan,
            history=state.conversation_history,
        )
        l_path = guided_learning_engine.generate_learning_path(
            state.question,
            topic=canonical_topic,
            plan=state.execution_plan,
        )

        state.recommended_questions = guided_qs

        if edu_dict:
            edu_dict["guided_questions"] = guided_qs
            edu_dict["learning_path"] = l_path.dict()
            state.provider_metadata["educational_response"] = edu_dict
            state.educational_response = edu_dict

        state.planner_reasoning.append(
            f"[Guided Learning Node] Generated {len(guided_qs)} follow-up questions & structured learning path."
        )
        logger.info(f"[Guided Learning Node] Successfully attached guided learning for topic '{l_path.current_topic}'")
    except Exception as e:
        logger.error(f"[Guided Learning Node] Error: {e}", exc_info=True)
        state.planner_reasoning.append(f"[Guided Learning Node] Error: {e}")

    return state
