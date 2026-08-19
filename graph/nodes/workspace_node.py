"""LangGraph Workspace Persistence Node for EKIP Educational Workflow."""

from graph.state import EKIPGraphState
from core.workspace import workspace_manager
from core.logger import get_logger

logger = get_logger("graph.nodes.workspace")


def workspace_persistence_node(state: EKIPGraphState) -> EKIPGraphState:
    """Stores educational response in active student learning session if requested."""
    edu_dict = state.provider_metadata.get("educational_response") or state.educational_response

    if not edu_dict:
        logger.warning("[Workspace Node] No educational response found in state to persist.")
        state.planner_reasoning.append("[Workspace Node] Skipped (No educational response found).")
        return state

    try:
        query = state.question
        title = f"Study Note: {query[:40]}"
        ai_explanation = edu_dict.get("ai_explanation", "")
        takeaways = edu_dict.get("key_takeaways", [])
        terms = edu_dict.get("important_terms", {})

        # Automatically store as a study note in workspace database
        note = workspace_manager.save_study_note(
            query=query,
            title=title,
            ai_explanation=ai_explanation,
            key_takeaways=takeaways,
            important_terms=terms,
        )

        state.provider_metadata["workspace_saved_note_id"] = note.id
        state.planner_reasoning.append(f"[Workspace Node] Persisted study note (ID: {note.id}) to student workspace database.")
        logger.info(f"[Workspace Node] Successfully persisted workspace study note for query '{query[:30]}...'")
    except Exception as e:
        logger.error(f"[Workspace Node] Workspace persistence error: {e}", exc_info=True)
        state.planner_reasoning.append(f"[Workspace Node] Error: {e}")

    return state
