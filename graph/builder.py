"""LangGraph Planning Graph Builder for EKIP Educational Workflow.

Graph Structure:
START -> Intent Node -> Difficulty Node -> Source Selection Node -> Retrieval Strategy Node -> Output Planning Node -> Execution Plan Node -> END
"""

from typing import Any, Dict, Optional, List
from graph.state import EKIPGraphState
from graph.nodes import (
    intent_node,
    difficulty_node,
    source_selection_node,
    retrieval_strategy_node,
    output_planning_node,
    execution_plan_node,
    knowledge_collection_node,
    knowledge_verification_node,
    evidence_ranking_node,
    knowledge_synthesis_node,
    guided_learning_node,
    workspace_persistence_node,
)

from core.logger import get_logger

logger = get_logger("graph.builder")


class EKIPPlanningGraphBuilder:
    """StateGraph Planning Builder executing state transitions through graph nodes."""

    def __init__(self, config: Optional[Any] = None):
        self.config = config
        self.is_compiled = False
        self._compiled_graph = None
        self._init_graph()

    def _init_graph(self):
        """Build graph transitions using LangGraph if available, or native StateGraph executor."""
        try:
            from langgraph.graph import StateGraph, START, END
            workflow = StateGraph(EKIPGraphState)

            workflow.add_node("intent", intent_node)
            workflow.add_node("difficulty", difficulty_node)
            workflow.add_node("source_selection", source_selection_node)
            workflow.add_node("retrieval_strategy", retrieval_strategy_node)
            workflow.add_node("output_planning", output_planning_node)
            workflow.add_node("execution_plan", execution_plan_node)
            workflow.add_node("knowledge_collection", knowledge_collection_node)
            workflow.add_node("knowledge_verification", knowledge_verification_node)
            workflow.add_node("evidence_ranking", evidence_ranking_node)
            workflow.add_node("knowledge_synthesis", knowledge_synthesis_node)
            workflow.add_node("guided_learning", guided_learning_node)
            workflow.add_node("workspace_persistence", workspace_persistence_node)

            workflow.add_edge(START, "intent")
            workflow.add_edge("intent", "difficulty")
            workflow.add_edge("difficulty", "source_selection")
            workflow.add_edge("source_selection", "retrieval_strategy")
            workflow.add_edge("retrieval_strategy", "output_planning")
            workflow.add_edge("output_planning", "execution_plan")
            workflow.add_edge("execution_plan", "knowledge_collection")
            workflow.add_edge("knowledge_collection", "knowledge_verification")
            workflow.add_edge("knowledge_verification", "evidence_ranking")
            workflow.add_edge("evidence_ranking", "knowledge_synthesis")
            workflow.add_edge("knowledge_synthesis", "guided_learning")
            workflow.add_edge("guided_learning", "workspace_persistence")
            workflow.add_edge("workspace_persistence", END)

            self._compiled_graph = workflow.compile()
            self.is_compiled = True
            logger.info("Compiled EKIP LangGraph StateGraph with 12 nodes successfully.")
        except Exception as e:
            logger.warning(f"LangGraph compile fallback to native sequential state runner: {e}")
            self.is_compiled = True

    def run_planning_pipeline(self, initial_state: EKIPGraphState) -> EKIPGraphState:
        """Run state transitions through graph nodes."""
        if getattr(initial_state, "execution_mode", "") == "chat_planning" or getattr(initial_state, "skip_synthesis", False):
            logger.info("[Planning Graph] Chat planning mode active: running planning nodes only.")
            state = initial_state
            state.planner_reasoning.append("[Planning Graph] Chat planning mode active: Skipped knowledge synthesis and workspace persistence.")
            state = intent_node(state)
            state = difficulty_node(state)
            state = source_selection_node(state)
            state = retrieval_strategy_node(state)
            state = output_planning_node(state)
            state = execution_plan_node(state)
            return state

        if self._compiled_graph is not None:
            try:
                res = self._compiled_graph.invoke(initial_state)
                if isinstance(res, dict):
                    return EKIPGraphState(**res)
                return res
            except Exception as err:
                logger.warning(f"LangGraph execution fallback to node pipeline: {err}")

        # Native node pipeline fallback
        state = initial_state
        state = intent_node(state)
        state = difficulty_node(state)
        state = source_selection_node(state)
        state = retrieval_strategy_node(state)
        state = output_planning_node(state)
        state = execution_plan_node(state)
        state = knowledge_collection_node(state)
        state = knowledge_verification_node(state)
        state = evidence_ranking_node(state)
        state = knowledge_synthesis_node(state)
        state = guided_learning_node(state)
        state = workspace_persistence_node(state)
        return state





    def invoke(self, input_data: Dict[str, Any]) -> EKIPGraphState:
        """Invoke planning graph with input question & conversation history."""
        if isinstance(input_data, dict):
            data = dict(input_data)
            if "user_query" in data and "question" not in data:
                data["question"] = data["user_query"]
            if "doc_filter" in data and "selected_docs" not in data:
                data["selected_docs"] = data["doc_filter"]
            state = EKIPGraphState(**data)
        else:
            state = input_data
        return self.run_planning_pipeline(state)


def create_ekip_planning_graph(config: Optional[Any] = None) -> EKIPPlanningGraphBuilder:
    """Factory function creating compiled EKIP planning graph."""
    return EKIPPlanningGraphBuilder(config)


# Legacy alias for backward compatibility
create_ekip_graph = create_ekip_planning_graph
EKIPGraphBuilder = EKIPPlanningGraphBuilder
