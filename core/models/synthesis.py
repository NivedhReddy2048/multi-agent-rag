"""Domain Models for EKIP Phase 2.5 Knowledge Synthesis, Response Composition & Guided Learning."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SynthesizedKnowledge(BaseModel):
    """Internal model produced by KnowledgeSynthesizer combining verified evidence."""

    query: str = Field(default="")
    primary_explanation: str = Field(default="")
    supporting_explanations: List[Dict[str, Any]] = Field(default_factory=list)
    conflicting_views: List[Dict[str, Any]] = Field(default_factory=list)
    key_takeaways: List[str] = Field(default_factory=list)
    important_terms: Dict[str, str] = Field(default_factory=dict, description="Glossary map: Term -> Definition")
    provenance_map: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.0)
    agreement: float = Field(default=0.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LearningPath(BaseModel):
    """4-tier structured learning path progression."""

    current_topic: str = Field(default="")
    prerequisites: List[str] = Field(default_factory=list)
    next_topics: List[str] = Field(default_factory=list)
    advanced_topics: List[str] = Field(default_factory=list)


class EducationalResponse(BaseModel):
    """Primary UI & Educational Response Model encapsulating layered learning content."""

    query: str = Field(default="")
    educational_mode: str = Field(default="detailed_explanation")

    # Layered Response Sections
    ai_explanation: str = Field(default="")
    uploaded_notes: List[Dict[str, Any]] = Field(default_factory=list)
    trusted_web: List[Dict[str, Any]] = Field(default_factory=list)
    wikipedia: List[Dict[str, Any]] = Field(default_factory=list)
    research: List[Dict[str, Any]] = Field(default_factory=list)
    books: List[Dict[str, Any]] = Field(default_factory=list)
    videos: List[Dict[str, Any]] = Field(default_factory=list)
    code_examples: List[Dict[str, Any]] = Field(default_factory=list)

    # Educational Enhancements
    key_takeaways: List[str] = Field(default_factory=list)
    important_terms: Dict[str, str] = Field(default_factory=dict)
    learning_summary: str = Field(default="")
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)

    # Guided Learning & Progression
    guided_questions: List[str] = Field(default_factory=list)
    learning_path: Optional[LearningPath] = Field(default=None)

    # Citations & Provenance
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    providers_used: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0)
    agreement: float = Field(default=0.0)
    synthesis_metadata: Dict[str, Any] = Field(default_factory=dict)
