"""Verification Domain Models & Multi-Dimensional Profiles for EKIP Phase 2.4."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from core.models.domain import KnowledgeResult


class VerificationProfile(BaseModel):
    """Multi-dimensional explainable verification profile for granular evidence assessment."""

    relevance_score: float = Field(default=0.0, description="Query semantic similarity & intent alignment (0-1)")
    credibility_score: float = Field(default=0.0, description="Base source authority & publisher weight (0-1)")
    agreement_score: float = Field(default=0.0, description="Cross-source corroboration & consensus (0-1)")
    freshness_score: float = Field(default=0.0, description="Recency & publication timeliness (0-1)")
    completeness_score: float = Field(default=0.0, description="Information depth & length completeness (0-1)")
    educational_value_score: float = Field(default=0.0, description="Educational clarity & instructional utility (0-1)")
    overall_score: float = Field(default=0.0, description="Weighted multi-dimensional verification score (0-1)")


class VerifiedKnowledgeResult(KnowledgeResult):
    """Enriched KnowledgeResult containing multi-dimensional verification profile and evidence metadata."""

    verification_score: float = Field(default=0.0)
    relevance_score: float = Field(default=0.0)
    credibility_score: float = Field(default=0.0)
    freshness_score: float = Field(default=0.0)
    agreement_score: float = Field(default=0.0)

    profile: Optional[VerificationProfile] = Field(default=None)
    duplicate_group: Optional[str] = Field(default=None)
    verification_notes: List[str] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    supporting_sources: List[str] = Field(default_factory=list)
    is_canonical: bool = Field(default=True)


class VerifiedKnowledgeCollection(BaseModel):
    """Container holding verified, scored, cross-corroborated, and ranked evidence objects."""

    query: str = Field(default="")
    execution_plan_id: str = Field(default="")
    verification_timestamp: str = Field(default="")
    total_latency_ms: float = Field(default=0.0)
    verified_results: List[VerifiedKnowledgeResult] = Field(default_factory=list)
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    duplicates: List[Dict[str, Any]] = Field(default_factory=list)
    overall_confidence: float = Field(default=0.0)
    overall_agreement: float = Field(default=0.0)
    verification_summary: str = Field(default="")
    ranking: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
