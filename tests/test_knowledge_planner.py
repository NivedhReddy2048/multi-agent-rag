"""Unit Test Suite for EKIP Phase 2.2 Knowledge Planner & LangGraph Orchestration."""

import pytest
from core.planner.enums import (
    EducationalIntent,
    DifficultyLevel,
    RetrievalStrategy,
    ExpectedOutputFormat,
    LatencyEstimate,
    CostEstimate,
)
from core.planner.rules import RuleBasedPlannerEngine
from core.planner.execution_plan import ExecutionPlan
from core.planner.knowledge_planner import knowledge_planner, ConcreteKnowledgePlanner
from graph.builder import create_ekip_planning_graph
from graph.state import EKIPGraphState
from core.models.domain import SourceType


def test_intent_classification():
    """Test deterministic educational intent classification."""
    intent, _ = RuleBasedPlannerEngine.classify_intent("Recommend latest GraphRAG papers", [])
    assert intent == EducationalIntent.RESEARCH

    intent, _ = RuleBasedPlannerEngine.classify_intent("Compare GPT-4 vs Llama 3", [])
    assert intent == EducationalIntent.COMPARISON

    intent, _ = RuleBasedPlannerEngine.classify_intent("Show me YouTube videos on linear algebra", [])
    assert intent == EducationalIntent.VIDEO_RECOMMENDATION

    intent, _ = RuleBasedPlannerEngine.classify_intent("Recommend books on quantum computing", [])
    assert intent == EducationalIntent.BOOK_RECOMMENDATION

    intent, _ = RuleBasedPlannerEngine.classify_intent("Summarize my uploaded lecture notes", [])
    assert intent == EducationalIntent.STUDY_NOTES

    intent, _ = RuleBasedPlannerEngine.classify_intent("How to fix Python recursion limit error", [])
    assert intent == EducationalIntent.PROGRAMMING_HELP


def test_difficulty_estimation():
    """Test difficulty level estimation based on vocabulary and context."""
    diff, _ = RuleBasedPlannerEngine.estimate_difficulty("What is AI?", [], EducationalIntent.CONCEPT_EXPLANATION)
    assert diff == DifficultyLevel.BEGINNER

    diff, _ = RuleBasedPlannerEngine.estimate_difficulty("Explain Transformer cross-attention architecture", [], EducationalIntent.CONCEPT_EXPLANATION)
    assert diff == DifficultyLevel.ADVANCED

    diff, _ = RuleBasedPlannerEngine.estimate_difficulty("Latest diffusion model research and asymptotic bounds", [], EducationalIntent.RESEARCH)
    assert diff == DifficultyLevel.RESEARCH

    # Multi-turn context progression
    history = [{"role": "user", "content": "1"}, {"role": "assistant", "content": "2"}, {"role": "user", "content": "3"}, {"role": "assistant", "content": "4"}]
    diff, _ = RuleBasedPlannerEngine.estimate_difficulty("Tell me more", history, EducationalIntent.CONCEPT_EXPLANATION)
    assert diff == DifficultyLevel.INTERMEDIATE


def test_source_selection():
    """Test source selection logic for various educational intents."""
    sources, _ = RuleBasedPlannerEngine.select_sources("Search arXiv papers for RAG", EducationalIntent.RESEARCH, DifficultyLevel.RESEARCH)
    assert SourceType.SEMANTIC_SCHOLAR in sources
    assert SourceType.ARXIV in sources

    sources, _ = RuleBasedPlannerEngine.select_sources("Summarize uploaded PDF notes", EducationalIntent.STUDY_NOTES, DifficultyLevel.INTERMEDIATE)
    assert SourceType.INTERNAL_DOCUMENT in sources

    sources, _ = RuleBasedPlannerEngine.select_sources("Recommend YouTube videos for Calculus", EducationalIntent.VIDEO_RECOMMENDATION, DifficultyLevel.BEGINNER)
    assert SourceType.VIDEO in sources


def test_retrieval_strategy_determination():
    """Test retrieval strategy classification."""
    strat, _ = RuleBasedPlannerEngine.determine_retrieval_strategy([SourceType.INTERNAL_DOCUMENT])
    assert strat == RetrievalStrategy.INTERNAL_ONLY

    strat, _ = RuleBasedPlannerEngine.determine_retrieval_strategy([SourceType.GENERAL_AI, SourceType.SEMANTIC_SCHOLAR, SourceType.ARXIV])
    assert strat == RetrievalStrategy.RESEARCH

    strat, _ = RuleBasedPlannerEngine.determine_retrieval_strategy([SourceType.GENERAL_AI, SourceType.VIDEO, SourceType.WIKIPEDIA])
    assert strat == RetrievalStrategy.EDUCATIONAL


def test_execution_plan_generation():
    """Test complete ExecutionPlan object generation."""
    plan = RuleBasedPlannerEngine.generate_plan("Compare Supervised vs Unsupervised Learning with videos")
    assert isinstance(plan, ExecutionPlan)
    assert plan.intent == EducationalIntent.COMPARISON or plan.intent == EducationalIntent.VIDEO_RECOMMENDATION
    assert len(plan.reasoning_steps) >= 5
    assert plan.estimated_latency in (LatencyEstimate.LOW, LatencyEstimate.MEDIUM, LatencyEstimate.HIGH)
    assert plan.estimated_cost in (CostEstimate.LOW, CostEstimate.MEDIUM, CostEstimate.HIGH)


def test_concrete_knowledge_planner_interface():
    """Test KnowledgePlanner interface implementation."""
    planner = ConcreteKnowledgePlanner()
    source_names = planner.plan("Explain Quantum Mechanics")
    assert isinstance(source_names, list)
    assert len(source_names) > 0

    exec_plan = planner.create_execution_plan("Explain Quantum Mechanics")
    assert isinstance(exec_plan, ExecutionPlan)


def test_langgraph_planning_pipeline():
    """Test full LangGraph state graph execution pipeline."""
    graph = create_ekip_planning_graph()
    state = graph.invoke({"question": "Explain Transformers architecture and recommend papers"})
    assert isinstance(state, EKIPGraphState)
    assert state.intent in (EducationalIntent.CONCEPT_EXPLANATION, EducationalIntent.RESEARCH)
    assert state.execution_plan is not None
    assert len(state.planner_reasoning) >= 5
    assert state.requires_research is True or SourceType.SEMANTIC_SCHOLAR in state.selected_sources
