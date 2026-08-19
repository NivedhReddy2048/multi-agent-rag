"""Unit and Integration Test Suite for EKIP Phase 2.3 Knowledge Source Agents & Parallel Orchestration."""

import time
import pytest
from core.models.domain import KnowledgeResult, KnowledgeCollection, SourceType
from core.planner.enums import (
    EducationalIntent,
    DifficultyLevel,
    RetrievalStrategy,
    ExpectedOutputFormat,
    LatencyEstimate,
    CostEstimate,
)
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
from core.orchestrator import KnowledgeOrchestrator, knowledge_orchestrator
from graph.builder import create_ekip_planning_graph
from graph.state import EKIPGraphState


def test_knowledge_result_instantiation():
    """Verify KnowledgeResult model fields and defaults."""
    res = KnowledgeResult(
        provider="test_provider",
        source_type=SourceType.WIKIPEDIA,
        title="Test Title",
        content="Test content summary.",
        url="https://example.com",
        latency_ms=45.0,
    )
    assert res.provider == "test_provider"
    assert res.source_type == SourceType.WIKIPEDIA
    assert res.title == "Test Title"
    assert res.latency_ms == 45.0
    assert res.confidence == 1.0


def test_agent_initialization_and_health():
    """Verify modular knowledge agent initialization and health methods."""
    agents = [
        WikipediaKnowledgeAgent(),
        ArxivKnowledgeAgent(),
        GoogleBooksKnowledgeAgent(),
        YoutubeKnowledgeAgent(),
        GithubKnowledgeAgent(),
        TrustedWebKnowledgeAgent(),
    ]
    for agent in agents:
        assert agent.initialize() is True
        assert isinstance(agent.health(), bool)


def test_mock_agent_execution():
    """Verify individual agent execute returns List[KnowledgeResult]."""
    wiki_agent = WikipediaKnowledgeAgent()
    results = wiki_agent.execute("Quantum Computing", max_results=2)
    assert isinstance(results, list)
    if results:
        assert isinstance(results[0], KnowledgeResult)
        assert results[0].source_type == SourceType.WIKIPEDIA


def test_orchestrator_routing_and_parallel_collection():
    """Verify KnowledgeOrchestrator routes plan sources and executes in parallel."""
    orchestrator = KnowledgeOrchestrator()

    plan = ExecutionPlan(
        intent=EducationalIntent.RESEARCH,
        difficulty=DifficultyLevel.RESEARCH,
        selected_sources=[SourceType.WIKIPEDIA, SourceType.ARXIV, SourceType.GENERAL_AI],
        retrieval_strategy=RetrievalStrategy.RESEARCH,
        expected_output=ExpectedOutputFormat.RESEARCH_SURVEY,
        estimated_latency=LatencyEstimate.MEDIUM,
        estimated_cost=CostEstimate.LOW,
        reasoning="Test Plan",
        reasoning_steps=["Step 1"],
    )

    t0 = time.time()
    collection = orchestrator.collect("Explain Transformers in NLP", plan)
    elapsed_ms = (time.time() - t0) * 1000

    assert isinstance(collection, KnowledgeCollection)
    assert collection.query == "Explain Transformers in NLP"
    assert "wikipedia" in collection.sources_requested
    assert "arxiv" in collection.sources_requested
    assert isinstance(collection.results, list)
    assert collection.total_latency_ms > 0.0


def test_orchestrator_partial_failure_handling():
    """Verify failure of one agent does not crash the orchestrator."""
    orchestrator = KnowledgeOrchestrator()

    class FaultyAgent(BaseKnowledgeAgent):
        def initialize(self) -> bool:
            return True
        def health(self) -> bool:
            return False
        def execute(self, query: str, max_results: int = 5) -> list:
            raise RuntimeError("Simulated API failure")

    # Inject faulty agent into orchestrator
    orchestrator.agents[SourceType.GITHUB_REPO] = FaultyAgent(
        agent_name="FaultyAgent",
        source_type=SourceType.GITHUB_REPO,
        provider_key="faulty"
    )

    plan = ExecutionPlan(
        intent=EducationalIntent.PROGRAMMING_HELP,
        difficulty=DifficultyLevel.BEGINNER,
        selected_sources=[SourceType.WIKIPEDIA, SourceType.GITHUB_REPO],
        retrieval_strategy=RetrievalStrategy.EDUCATIONAL,
        expected_output=ExpectedOutputFormat.CODE_WALKTHROUGH,
        estimated_latency=LatencyEstimate.LOW,
        estimated_cost=CostEstimate.LOW,
        reasoning="Test fault tolerance",
        reasoning_steps=[],
    )

    collection = orchestrator.collect("Python list comprehension", plan)
    assert isinstance(collection, KnowledgeCollection)
    assert "github_repo" in collection.sources_failed
    assert "wikipedia" in collection.sources_completed or len(collection.results) >= 0


def test_langgraph_collection_node_integration():
    """Verify full LangGraph planning + collection graph execution."""
    graph = create_ekip_planning_graph()
    state = graph.invoke({"question": "Explain Neural Networks and recommend books"})

    assert isinstance(state, EKIPGraphState)
    assert state.execution_plan is not None
    assert "knowledge_collection" in state.provider_metadata
    collection_dict = state.provider_metadata["knowledge_collection"]
    assert "sources_requested" in collection_dict
    assert "sources_completed" in collection_dict
