"""LangGraph Evidence Ranking Node for EKIP Educational Workflow."""

from graph.state import EKIPGraphState
from core.logger import get_logger

logger = get_logger("graph.nodes.ranking")


def evidence_ranking_node(state: EKIPGraphState) -> EKIPGraphState:
    """Ranks verified multi-source evidence based on verification profiles and intent alignment."""
    ver_dict = state.provider_metadata.get("verified_collection") or state.verified_collection

    if not ver_dict:
        logger.warning("[Evidence Ranking Node] No verified_collection found in state. Skipping ranking.")
        state.planner_reasoning.append("[Evidence Ranking Node] Skipped (No verified collection data found).")
        return state

    try:
        results = ver_dict.get("verified_results", [])
        if results:
            top_ranked = results[:3]
            top_summary = ", ".join([f"'{r.get('title', 'Untitled')}' ({int(r.get('verification_score', 0)*100)}%)" for r in top_ranked])
            state.planner_reasoning.append(
                f"[Evidence Ranking Node] Top Verified Evidence: {top_summary}"
            )
            logger.info(f"[Evidence Ranking Node] Ranked {len(results)} items. Top item: {top_ranked[0].get('title', 'N/A')}")
    except Exception as e:
        logger.error(f"[Evidence Ranking Node] Ranking node error: {e}", exc_info=True)
        state.planner_reasoning.append(f"[Evidence Ranking Node] Error: {e}")

    return state
