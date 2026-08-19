"""Abstract Interfaces for EKIP Knowledge Planner, Router, Verifier, Ranker, and Summarizer."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from core.models.domain import (
    KnowledgeSource,
    KnowledgeResult,
    LearningSummary,
    RecommendedQuestion,
)


class KnowledgePlanner(ABC):
    """Abstract Planner interface deciding which knowledge sources to query based on intent."""

    @abstractmethod
    def plan(self, question: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Evaluate question semantics and return list of target provider names to invoke.

        Example output: ["groq", "uploaded_notes", "wikipedia", "youtube"]
        """
        pass


class KnowledgeRouter(ABC):
    """Abstract Router interface executing fan-out queries to planned collectors."""

    @abstractmethod
    def route_and_collect(
        self, question: str, selected_sources: List[str]
    ) -> Dict[str, List[KnowledgeResult]]:
        """Dispatch question to selected collectors and collect standardized KnowledgeResult lists."""
        pass


class KnowledgeVerifier(ABC):
    """Abstract Verifier interface auditing knowledge quality, factuality, and relevance (CRAG Evolution)."""

    @abstractmethod
    def verify(
        self, query: str, collected_results: Dict[str, List[KnowledgeResult]]
    ) -> Dict[str, List[KnowledgeResult]]:
        """Audit and filter low-confidence or irrelevant knowledge results."""
        pass


class KnowledgeRanker(ABC):
    """Abstract Ranker interface scoring cross-source evidence and resolving conflicts."""

    @abstractmethod
    def rank(
        self, query: str, verified_results: Dict[str, List[KnowledgeResult]]
    ) -> List[KnowledgeResult]:
        """Rank and return ordered list of top evidence across all sources."""
        pass


class LearningSummarizer(ABC):
    """Abstract Summarizer interface producing final consensus synthesis and recommended questions."""

    @abstractmethod
    def summarize(
        self, query: str, ranked_evidence: List[KnowledgeResult]
    ) -> LearningSummary:
        """Synthesize verified evidence into structured LearningSummary."""
        pass

    @abstractmethod
    def generate_recommendations(
        self, query: str, summary: str
    ) -> List[RecommendedQuestion]:
        """Generate 3 guided learning follow-up questions."""
        pass
