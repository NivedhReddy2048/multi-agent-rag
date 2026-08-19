"""LangGraph Knowledge Verification Node for EKIP Educational Intelligence Engine."""

from graph.state import EKIPGraphState
from core.models.domain import KnowledgeCollection, KnowledgeResult
from core.verification import knowledge_verifier
from core.logger import get_logger

logger = get_logger("graph.nodes.verification")


def knowledge_verification_node(state: EKIPGraphState) -> EKIPGraphState:
    """Evaluates, verifies, scores, and detects conflicts across collected multi-source evidence."""
    col_dict = state.provider_metadata.get("knowledge_collection")

    if not col_dict:
        logger.warning("[Knowledge Verification Node] No knowledge_collection found in provider_metadata. Skipping verification.")
        state.planner_reasoning.append("[Knowledge Verification Node] Skipped (No collection data found).")
        return state

    try:
        raw_results = [KnowledgeResult(**r) for r in col_dict.get("results", [])]
        collection = KnowledgeCollection(
            query=col_dict.get("query", state.question),
            execution_plan_id=col_dict.get("execution_plan_id", ""),
            collection_timestamp=col_dict.get("collection_timestamp", ""),
            total_latency_ms=col_dict.get("total_latency_ms", 0.0),
            sources_requested=col_dict.get("sources_requested", []),
            sources_completed=col_dict.get("sources_completed", []),
            sources_failed=col_dict.get("sources_failed", []),
            results=raw_results,
            provider_latencies=col_dict.get("provider_latencies", {}),
            metadata=col_dict.get("metadata", {}),
        )

        verified_collection = knowledge_verifier.verify_collection(collection, state.execution_plan)

        ver_dict = verified_collection.dict()
        state.provider_metadata["verified_collection"] = ver_dict
        state.verified_collection = ver_dict

        state.confidence = verified_collection.overall_confidence
        state.planner_reasoning.append(
            f"[Knowledge Verification Node] {verified_collection.verification_summary}"
        )
        logger.info(f"[Knowledge Verification Node] Verified {len(verified_collection.verified_results)} evidence items. Overall confidence: {verified_collection.overall_confidence}")
    except Exception as e:
        logger.error(f"[Knowledge Verification Node] Verification failed: {e}", exc_info=True)
        state.planner_reasoning.append(f"[Knowledge Verification Node] Verification error: {e}")

    return state
