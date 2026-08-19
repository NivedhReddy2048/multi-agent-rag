"""EKIP Domain Models Package."""

from core.models.domain import (
    SourceType,
    KnowledgeSource,
    KnowledgeResult,
    KnowledgeCollection,
    LearningResource,
    ResearchPaper,
    BookRecommendation,
    VideoRecommendation,
    RecommendedQuestion,
    LearningSummary,
)
from core.models.verification import (
    VerificationProfile,
    VerifiedKnowledgeResult,
    VerifiedKnowledgeCollection,
)
from core.models.synthesis import (
    SynthesizedKnowledge,
    LearningPath,
    EducationalResponse,
)
from core.models.workspace import (
    Bookmark,
    StudyNote,
    Notebook,
    StudyCollection,
    LearningSession,
    WorkspaceProgress,
)

__all__ = [
    "SourceType",
    "KnowledgeSource",
    "KnowledgeResult",
    "KnowledgeCollection",
    "VerificationProfile",
    "VerifiedKnowledgeResult",
    "VerifiedKnowledgeCollection",
    "SynthesizedKnowledge",
    "LearningPath",
    "EducationalResponse",
    "Bookmark",
    "StudyNote",
    "Notebook",
    "StudyCollection",
    "LearningSession",
    "WorkspaceProgress",
    "LearningResource",
    "ResearchPaper",
    "BookRecommendation",
    "VideoRecommendation",
    "RecommendedQuestion",
    "LearningSummary",
]




