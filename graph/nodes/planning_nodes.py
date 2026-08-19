"""LangGraph Planning Nodes for EKIP Educational Planning Graph."""

from graph.state import EKIPGraphState
from core.planner.rules import RuleBasedPlannerEngine
from core.logger import get_logger

logger = get_logger("graph.nodes.planning")


def intent_node(state: EKIPGraphState) -> EKIPGraphState:
    """Classify educational intent node."""
    intent, reason = RuleBasedPlannerEngine.classify_intent(state.question, state.conversation_history)
    state.intent = intent
    state.planner_reasoning.append(f"[Intent Node] Intent classified as '{intent.value}': {reason}")
    logger.debug(f"[Graph Node] Intent Node -> {intent.value}")
    return state


def difficulty_node(state: EKIPGraphState) -> EKIPGraphState:
    """Estimate difficulty level node."""
    difficulty, reason = RuleBasedPlannerEngine.estimate_difficulty(state.question, state.conversation_history, state.intent)
    state.difficulty = difficulty
    state.planner_reasoning.append(f"[Difficulty Node] Difficulty estimated as '{difficulty.value}': {reason}")
    logger.debug(f"[Graph Node] Difficulty Node -> {difficulty.value}")
    return state


def source_selection_node(state: EKIPGraphState) -> EKIPGraphState:
    """Identify appropriate knowledge sources node."""
    target_docs = RuleBasedPlannerEngine.resolve_target_documents(state.question, state.selected_docs)
    strat, strat_reason = RuleBasedPlannerEngine.determine_source_strategy(state.question, state.intent, state.conversation_history, target_docs=target_docs)
    sources, reason = RuleBasedPlannerEngine.select_sources(state.question, state.intent, state.difficulty, strat)
    state.source_strategy = strat
    state.selected_sources = sources
    state.recommended_sources = [s.value for s in sources]
    state.planner_reasoning.append(f"[Source Strategy Node] Source strategy selected '{strat.value}': {strat_reason}")
    state.planner_reasoning.append(f"[Source Selection Node] Selected sources {[s.value for s in sources]}: {reason}")
    logger.debug(f"[Graph Node] Source Selection Node -> Strategy={strat.value}, Sources={[s.value for s in sources]}")
    return state



def retrieval_strategy_node(state: EKIPGraphState) -> EKIPGraphState:
    """Choose retrieval strategy node."""
    strategy, reason = RuleBasedPlannerEngine.determine_retrieval_strategy(state.selected_sources)
    state.retrieval_strategy = strategy
    state.planner_reasoning.append(f"[Retrieval Strategy Node] Strategy selected '{strategy.value}': {reason}")
    logger.debug(f"[Graph Node] Retrieval Strategy Node -> {strategy.value}")
    return state


def output_planning_node(state: EKIPGraphState) -> EKIPGraphState:
    """Determine expected output format node."""
    output_format = RuleBasedPlannerEngine.determine_expected_output(state.intent)
    state.expected_output = output_format
    state.planner_reasoning.append(f"[Output Planning Node] Expected output format set to '{output_format.value}'")
    logger.debug(f"[Graph Node] Output Planning Node -> {output_format.value}")
    return state


def execution_plan_node(state: EKIPGraphState) -> EKIPGraphState:
    """Compile final ExecutionPlan contract node."""
    docs_context = state.selected_docs or None
    plan = RuleBasedPlannerEngine.generate_plan(state.question, state.conversation_history, available_docs=docs_context)
    state.execution_plan = plan
    state.source_strategy = plan.source_strategy
    state.estimated_latency = plan.estimated_latency
    state.estimated_cost = plan.estimated_cost
    state.requires_internal_documents = plan.requires_internal_documents
    state.requires_external_search = plan.requires_external_search
    state.requires_research = plan.requires_research
    state.requires_books = plan.requires_books
    state.requires_videos = plan.requires_videos
    state.requires_code = plan.requires_code
    state.planner_reasoning.append(f"[Execution Plan Node] Generated final ExecutionPlan with {len(plan.reasoning_steps)} reasoning steps.")
    logger.info(f"[Graph Node] Execution Plan Node complete. Intent={state.intent.value}, SourceStrategy={state.source_strategy.value}, Strategy={state.retrieval_strategy.value}")
    return state
