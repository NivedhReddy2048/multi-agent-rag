"""EKIP LangGraph Planning State Definition for Educational Orchestration."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from core.models.domain import SourceType
from core.planner.enums import (
    EducationalIntent,
    DifficultyLevel,
    SourceStrategy,
    RetrievalStrategy,
    ExpectedOutputFormat,
    LatencyEstimate,
    CostEstimate,
)
from core.planner.execution_plan import ExecutionPlan


class EKIPGraphState(BaseModel):
    """Typed State Definition for EKIP Multi-Agent Graph Planning Orchestrator."""

    # Primary Input & Context
    question: str = Field(default="", description="Original user query / student question")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Stateful conversation chat context")
    selected_docs: List[str] = Field(default_factory=list, description="Optional active document filters passed into planning graph")

    # Planning & Decision Fields (Phase 2.2)
    intent: EducationalIntent = Field(default=EducationalIntent.CONCEPT_EXPLANATION)
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.INTERMEDIATE)
    source_strategy: SourceStrategy = Field(default=SourceStrategy.GENERAL_KNOWLEDGE)
    selected_sources: List[SourceType] = Field(default_factory=list)
    retrieval_strategy: RetrievalStrategy = Field(default=RetrievalStrategy.HYBRID)
    expected_output: ExpectedOutputFormat = Field(default=ExpectedOutputFormat.DETAILED_EXPLANATION)
    execution_plan: Optional[ExecutionPlan] = Field(default=None)

    planner_reasoning: List[str] = Field(default_factory=list)
    estimated_latency: LatencyEstimate = Field(default=LatencyEstimate.MEDIUM)
    estimated_cost: CostEstimate = Field(default=CostEstimate.LOW)
    recommended_sources: List[str] = Field(default_factory=list)
    provider_constraints: Dict[str, Any] = Field(default_factory=dict)

    # Resource Flags
    requires_internal_documents: bool = Field(default=False)
    requires_external_search: bool = Field(default=False)
    requires_research: bool = Field(default=False)
    requires_books: bool = Field(default=False)
    requires_videos: bool = Field(default=False)
    requires_code: bool = Field(default=False)

    # Multi-Source Knowledge Collections & Verification (Phase 2.3 & 2.4)
    retrieved_documents: List[Dict[str, Any]] = Field(default_factory=list)
    retrieved_web: List[Dict[str, Any]] = Field(default_factory=list)
    retrieved_research: List[Dict[str, Any]] = Field(default_factory=list)
    retrieved_books: List[Dict[str, Any]] = Field(default_factory=list)
    retrieved_videos: List[Dict[str, Any]] = Field(default_factory=list)
    retrieved_wikipedia: List[Dict[str, Any]] = Field(default_factory=list)

    # Verification & Synthesis Collection Containers (Phase 2.4 & 2.5)
    execution_mode: str = Field(default="full", description="Graph execution mode: 'full' or 'chat_planning'")
    skip_synthesis: bool = Field(default=False, description="Flag to skip standalone knowledge synthesis node in chat planning mode")
    verified_collection: Optional[Dict[str, Any]] = Field(default=None)
    educational_response: Optional[Dict[str, Any]] = Field(default=None)

    # Telemetry & Quality
    provider_metadata: Dict[str, Any] = Field(default_factory=dict)


    confidence: float = Field(default=0.0)
    faithfulness: float = Field(default=0.0)
    final_summary: str = Field(default="")
    recommended_questions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
