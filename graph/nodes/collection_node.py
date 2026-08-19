"""LangGraph Knowledge Collection Node for EKIP Parallel Knowledge Collection."""

from graph.state import EKIPGraphState
from core.orchestrator.knowledge_orchestrator import knowledge_orchestrator
from core.models.domain import SourceType
from core.logger import get_logger

logger = get_logger("graph.nodes.collection")


def knowledge_collection_node(state: EKIPGraphState) -> EKIPGraphState:
    """Invokes KnowledgeOrchestrator to collect standardized KnowledgeResults across selected agents."""
    if not state.execution_plan:
        logger.warning("[Knowledge Collection Node] No ExecutionPlan found in state. Skipping collection.")
        return state

    logger.info(f"[Knowledge Collection Node] Starting parallel collection for '{state.question[:30]}...'")

    try:
        collection = knowledge_orchestrator.collect(state.question, state.execution_plan)

        # Categorize retrieved KnowledgeResults into EKIPGraphState multi-source lists
        for res in collection.results:
            res_dict = res.dict()
            st_val = res.source_type.value if hasattr(res.source_type, "value") else str(res.source_type)

            if st_val == SourceType.INTERNAL_DOCUMENT.value:
                state.retrieved_documents.append(res_dict)
            elif st_val in (SourceType.TRUSTED_WEB.value, SourceType.FIRE_CRAWL.value, SourceType.JINA_READER.value):
                state.retrieved_web.append(res_dict)
            elif st_val in (SourceType.SEMANTIC_SCHOLAR.value, SourceType.ARXIV.value, SourceType.RESEARCH_PAPER.value):
                state.retrieved_research.append(res_dict)
            elif st_val in (SourceType.BOOK.value, SourceType.GOOGLE_BOOKS.value):
                state.retrieved_books.append(res_dict)
            elif st_val == SourceType.VIDEO.value:
                state.retrieved_videos.append(res_dict)
            elif st_val == SourceType.WIKIPEDIA.value:
                state.retrieved_wikipedia.append(res_dict)

        state.provider_metadata["knowledge_collection"] = collection.dict()
        state.planner_reasoning.append(
            f"[Knowledge Collection Node] Parallel collection complete in {int(collection.total_latency_ms)}ms. "
            f"Completed: {collection.sources_completed}, Failed: {collection.sources_failed}, Total Items: {len(collection.results)}"
        )
        logger.info(f"[Knowledge Collection Node] Finished. Total collected: {len(collection.results)} items across {len(collection.sources_completed)} sources.")
    except Exception as e:
        logger.error(f"[Knowledge Collection Node] Collection failed: {e}", exc_info=True)
        state.planner_reasoning.append(f"[Knowledge Collection Node] Error during collection: {e}")

    return state
