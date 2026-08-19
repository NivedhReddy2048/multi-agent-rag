"""LangGraph Knowledge Synthesis Node for EKIP Educational Workflow."""

from graph.state import EKIPGraphState
from core.models.verification import VerifiedKnowledgeCollection, VerifiedKnowledgeResult
from core.synthesis import knowledge_synthesizer, response_composer
from core.logger import get_logger

logger = get_logger("graph.nodes.synthesis")


def knowledge_synthesis_node(state: EKIPGraphState) -> EKIPGraphState:
    """Fuses verified knowledge evidence into SynthesizedKnowledge and composes initial EducationalResponse."""
    if state.execution_mode == "chat_planning" or state.skip_synthesis:
        logger.info("[Knowledge Synthesis Node] Skipping synthesis in chat_planning mode (deferred to OrchestratorAgent).")
        state.planner_reasoning.append(
            "[Knowledge Synthesis Node] Skipped (Chat planning mode active; answer synthesis deferred to OrchestratorAgent)."
        )
        return state

    ver_dict = state.provider_metadata.get("verified_collection") or state.verified_collection

    if not ver_dict:
        logger.warning("[Knowledge Synthesis Node] No verified_collection found in state. Skipping synthesis.")
        state.planner_reasoning.append("[Knowledge Synthesis Node] Skipped (No verified collection found).")
        return state

    try:
        raw_verified = [VerifiedKnowledgeResult(**r) for r in ver_dict.get("verified_results", [])]
        collection = VerifiedKnowledgeCollection(
            query=ver_dict.get("query", state.question),
            execution_plan_id=ver_dict.get("execution_plan_id", ""),
            verification_timestamp=ver_dict.get("verification_timestamp", ""),
            total_latency_ms=ver_dict.get("total_latency_ms", 0.0),
            verified_results=raw_verified,
            conflicts=ver_dict.get("conflicts", []),
            duplicates=ver_dict.get("duplicates", []),
            overall_confidence=ver_dict.get("overall_confidence", 0.0),
            overall_agreement=ver_dict.get("overall_agreement", 0.0),
            verification_summary=ver_dict.get("verification_summary", ""),
            ranking=ver_dict.get("ranking", []),
            metadata=ver_dict.get("metadata", {}),
        )

        syn_knowledge = knowledge_synthesizer.synthesize(collection, state.execution_plan, state.conversation_history)
        edu_response = response_composer.compose_response(syn_knowledge, collection, state.execution_plan, state.conversation_history)

        resp_dict = edu_response.dict()
        state.provider_metadata["educational_response"] = resp_dict
        state.educational_response = resp_dict
        state.final_summary = edu_response.learning_summary

        state.planner_reasoning.append(
            f"[Knowledge Synthesis Node] Synthesized evidence from {len(edu_response.providers_used)} providers. Confidence: {int(edu_response.confidence*100)}%."
        )
        logger.info(f"[Knowledge Synthesis Node] Synthesis complete for query: '{state.question[:30]}...'")
    except Exception as e:
        logger.error(f"[Knowledge Synthesis Node] Synthesis failed: {e}", exc_info=True)
        state.planner_reasoning.append(f"[Knowledge Synthesis Node] Error: {e}")

    return state
