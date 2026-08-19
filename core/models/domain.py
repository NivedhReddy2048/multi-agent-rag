"""EKIP Educational Domain Models for Future Multi-Source Knowledge Aggregation."""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    INTERNAL_DOCUMENT = "internal_document"
    GENERAL_AI = "general_ai"
    TRUSTED_WEB = "trusted_web"
    WIKIPEDIA = "wikipedia"
    RESEARCH_PAPER = "research_paper"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    ARXIV = "arxiv"
    BOOK = "book"
    GOOGLE_BOOKS = "google_books"
    VIDEO = "video"
    GITHUB_REPO = "github_repo"
    FIRE_CRAWL = "firecrawl"
    JINA_READER = "jina_reader"



class KnowledgeSource(BaseModel):
    """Metadata representing a registered knowledge source origin."""

    source_id: str
    name: str
    source_type: SourceType
    provider: str
    confidence_score: float = 0.0
    url: Optional[str] = None
    attribution: Optional[str] = None


class KnowledgeResult(BaseModel):
    """Generic standardized payload output retrieved from any knowledge source agent."""

    provider: str = Field(default="unknown")
    source_type: SourceType = Field(default=SourceType.GENERAL_AI)
    title: str = Field(default="")
    content: str = Field(default="")
    summary: Optional[str] = Field(default=None)
    url: Optional[str] = Field(default=None)
    authors: List[str] = Field(default_factory=list)
    published_date: Optional[str] = Field(default=None)
    confidence: float = Field(default=1.0)
    latency_ms: float = Field(default=0.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    raw_response: Optional[Any] = Field(default=None)

    # Legacy support
    source: Optional[KnowledgeSource] = Field(default=None)
    snippet: Optional[str] = Field(default=None)
    score: float = Field(default=0.0)


class KnowledgeCollection(BaseModel):
    """Unified container encapsulating multi-source retrieval outputs and performance metrics."""

    query: str = Field(default="")
    execution_plan_id: str = Field(default="")
    collection_timestamp: str = Field(default="")
    total_latency_ms: float = Field(default=0.0)
    sources_requested: List[str] = Field(default_factory=list)
    sources_completed: List[str] = Field(default_factory=list)
    sources_failed: List[str] = Field(default_factory=list)
    results: List[KnowledgeResult] = Field(default_factory=list)
    provider_latencies: Dict[str, float] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)



class LearningResource(BaseModel):
    """Base class for educational media and reference resources."""

    title: str
    description: str
    resource_type: str
    url: Optional[str] = None
    source_provider: str


class ResearchPaper(LearningResource):
    """Academic research paper domain model (Semantic Scholar / arXiv)."""

    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    venue: Optional[str] = None
    citation_count: int = 0
    pdf_url: Optional[str] = None
    abstract: str = ""

    def __init__(self, **data):
        if "resource_type" not in data:
            data["resource_type"] = "research_paper"
        super().__init__(**data)


class BookRecommendation(LearningResource):
    """Book recommendation domain model (Google Books)."""

    authors: List[str] = Field(default_factory=list)
    publisher: Optional[str] = None
    published_date: Optional[str] = None
    preview_link: Optional[str] = None

    def __init__(self, **data):
        if "resource_type" not in data:
            data["resource_type"] = "book"
        super().__init__(**data)


class VideoRecommendation(LearningResource):
    """Educational video recommendation domain model (YouTube)."""

    channel: str = ""
    duration: Optional[str] = None
    video_url: str = ""
    thumbnail: Optional[str] = None

    def __init__(self, **data):
        if "resource_type" not in data:
            data["resource_type"] = "video"
        super().__init__(**data)


class RecommendedQuestion(BaseModel):
    """Follow-up recommendation question model."""

    question_id: str
    question_text: str
    rationale: Optional[str] = None
    category: str = "continued_learning"


class LearningSummary(BaseModel):
    """Final synthesized multi-source consensus learning summary model."""

    query: str
    ai_explanation: str
    final_synthesis: str
    agreements: List[str] = Field(default_factory=list)
    discrepancies: List[str] = Field(default_factory=list)
    key_takeaways: List[str] = Field(default_factory=list)
    sources: List[KnowledgeSource] = Field(default_factory=list)
    recommended_questions: List[RecommendedQuestion] = Field(default_factory=list)
