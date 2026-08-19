"""EKIP Parallel Knowledge Orchestrator executing ExecutionPlan contracts via concurrent source agents."""

import time
import uuid
import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.models.domain import KnowledgeResult, KnowledgeCollection, SourceType
from core.planner.execution_plan import ExecutionPlan
from agents.sources import (
    BaseKnowledgeAgent,
    DocumentKnowledgeAgent,
    GeneralAIKnowledgeAgent,
    TrustedWebKnowledgeAgent,
    WikipediaKnowledgeAgent,
    SemanticScholarKnowledgeAgent,
    ArxivKnowledgeAgent,
    GoogleBooksKnowledgeAgent,
    YoutubeKnowledgeAgent,
    GithubKnowledgeAgent,
)
from core.logger import get_logger

logger = get_logger("core.orchestrator.knowledge_orchestrator")


class KnowledgeOrchestrator:
    """Orchestrates parallel, fault-tolerant collection across modular Knowledge Source Agents."""

    def __init__(self):
        # Register available knowledge agent singletons
        self.agents: Dict[SourceType, BaseKnowledgeAgent] = {
            SourceType.INTERNAL_DOCUMENT: DocumentKnowledgeAgent(),
            SourceType.GENERAL_AI: GeneralAIKnowledgeAgent(),
            SourceType.TRUSTED_WEB: TrustedWebKnowledgeAgent(),
            SourceType.WIKIPEDIA: WikipediaKnowledgeAgent(),
            SourceType.SEMANTIC_SCHOLAR: SemanticScholarKnowledgeAgent(),
            SourceType.ARXIV: ArxivKnowledgeAgent(),
            SourceType.BOOK: GoogleBooksKnowledgeAgent(),
            SourceType.GOOGLE_BOOKS: GoogleBooksKnowledgeAgent(),
            SourceType.VIDEO: YoutubeKnowledgeAgent(),
            SourceType.GITHUB_REPO: GithubKnowledgeAgent(),
        }

    def _get_agent_for_source(self, source: SourceType) -> Optional[BaseKnowledgeAgent]:
        return self.agents.get(source)

    def collect(self, query: str, plan: ExecutionPlan, timeout_seconds: float = 10.0) -> KnowledgeCollection:
        """Execute planner-requested knowledge source agents concurrently and collect standardized results."""
        t0 = time.time()
        plan_id = str(uuid.uuid4())[:8]
        timestamp = datetime.datetime.now().isoformat()

        requested_sources = [s.value if hasattr(s, "value") else str(s) for s in plan.selected_sources]
        logger.info(f"KnowledgeOrchestrator initiating collection for '{query[:30]}...' | Plan ID: {plan_id} | Requested: {requested_sources}")

        target_agents: Dict[str, BaseKnowledgeAgent] = {}
        for src in plan.selected_sources:
            agent = self._get_agent_for_source(src)
            if agent:
                target_agents[src.value if hasattr(src, "value") else str(src)] = agent

        completed_sources: List[str] = []
        failed_sources: List[str] = []
        all_results: List[KnowledgeResult] = []
        provider_latencies: Dict[str, float] = {}

        def _worker_task(src_key: str, agent_obj: BaseKnowledgeAgent) -> Tuple_Task_Output:
            worker_t0 = time.time()
            try:
                if not agent_obj.is_initialized:
                    agent_obj.initialize()
                if isinstance(agent_obj, DocumentKnowledgeAgent) and getattr(plan, "target_documents", None):
                    res_list = agent_obj.execute(query, max_results=5, target_documents=plan.target_documents)
                else:
                    res_list = agent_obj.execute(query, max_results=5)
                w_lat = (time.time() - worker_t0) * 1000
                return src_key, res_list, w_lat, None
            except Exception as exc:
                w_lat = (time.time() - worker_t0) * 1000
                return src_key, [], w_lat, str(exc)


        # Execute selected agents concurrently
        if target_agents:
            with ThreadPoolExecutor(max_workers=min(8, len(target_agents))) as executor:
                future_map = {
                    executor.submit(_worker_task, src_name, agent): src_name
                    for src_name, agent in target_agents.items()
                }

                for future in as_completed(future_map):
                    src_name = future_map[future]
                    try:
                        key, res_list, lat, err = future.result(timeout=timeout_seconds)
                        provider_latencies[key] = lat
                        if err is None:
                            completed_sources.append(key)
                            all_results.extend(res_list)
                            logger.debug(f"[Orchestrator Worker] '{key}' completed in {int(lat)}ms with {len(res_list)} items.")
                        else:
                            failed_sources.append(key)
                            logger.warning(f"[Orchestrator Worker] '{key}' failed after {int(lat)}ms: {err}")
                    except Exception as exc:
                        failed_sources.append(src_name)
                        logger.error(f"[Orchestrator Worker] '{src_name}' timed out or threw exception: {exc}")

        total_lat = (time.time() - t0) * 1000
        logger.info(
            f"KnowledgeOrchestrator collection finished in {int(total_lat)}ms | "
            f"Completed: {len(completed_sources)} | Failed: {len(failed_sources)} | Total Items: {len(all_results)}"
        )

        return KnowledgeCollection(
            query=query,
            execution_plan_id=plan_id,
            collection_timestamp=timestamp,
            total_latency_ms=total_lat,
            sources_requested=requested_sources,
            sources_completed=completed_sources,
            sources_failed=failed_sources,
            results=all_results,
            provider_latencies=provider_latencies,
            metadata={
                "intent": plan.intent.value if hasattr(plan.intent, "value") else str(plan.intent),
                "strategy": plan.retrieval_strategy.value if hasattr(plan.retrieval_strategy, "value") else str(plan.retrieval_strategy),
            }
        )


# Task output typing helper
Tuple_Task_Output = Any

# Global singleton instance
knowledge_orchestrator = KnowledgeOrchestrator()
