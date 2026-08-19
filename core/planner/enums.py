"""EKIP Educational Enums for Intent, Difficulty, Strategy, and Output Planning."""

from enum import Enum


class DocumentUsageMode(str, Enum):
    REQUIRED = "required"
    PREFERRED = "preferred"
    OPTIONAL = "optional"
    EXCLUDED = "excluded"


class SourceRole(str, Enum):
    FACTUAL_EVIDENCE = "factual_evidence"
    LEARNING_RESOURCE = "learning_resource"


class EducationalIntent(str, Enum):
    CONCEPT_EXPLANATION = "concept_explanation"
    TOPIC_SUMMARY = "topic_summary"
    COMPARISON = "comparison"
    PROGRAMMING_HELP = "programming_help"
    RESEARCH = "research"
    INTERVIEW_PREPARATION = "interview_preparation"
    EXAM_PREPARATION = "exam_preparation"
    BOOK_RECOMMENDATION = "book_recommendation"
    VIDEO_RECOMMENDATION = "video_recommendation"
    STUDY_NOTES = "study_notes"
    FLASHCARDS = "flashcards"
    QUIZ_GENERATION = "quiz_generation"
    PRACTICE_QUIZ = "practice_quiz"
    ROADMAP = "roadmap"
    ASSIGNMENT_HELP = "assignment_help"
    CAREER_GUIDANCE = "career_guidance"
    DOCUMENT_QUERY = "document_query"
    FACTUAL_LOOKUP = "factual_lookup"
    RESEARCH_DISCOVERY = "research_discovery"
    CODE_RESOURCE_RECOMMENDATION = "code_resource_recommendation"
    WEB_INFORMATION = "web_information"
    FOLLOW_UP = "follow_up"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    RESEARCH = "research"


class SourceStrategy(str, Enum):
    GENERAL_KNOWLEDGE = "general_knowledge"
    DOCUMENT_AUGMENTED = "document_augmented"
    DOCUMENT_ONLY = "document_only"
    WEB_AUGMENTED = "web_augmented"
    RESEARCH = "research"
    HYBRID = "hybrid"


class RetrievalStrategy(str, Enum):
    INTERNAL_ONLY = "internal_only"
    EXTERNAL_ONLY = "external_only"
    HYBRID = "hybrid"
    RESEARCH = "research"
    EDUCATIONAL = "educational"


class ExpectedOutputFormat(str, Enum):
    DETAILED_EXPLANATION = "detailed_explanation"
    COMPARISON_TABLE = "comparison_table"
    SUMMARY = "summary"
    RESEARCH_SURVEY = "research_survey"
    STUDY_NOTES = "study_notes"
    QUIZ = "quiz"
    FLASHCARDS = "flashcards"
    LEARNING_ROADMAP = "learning_roadmap"
    CODE_WALKTHROUGH = "code_walkthrough"
    BOOK_LIST = "book_list"
    VIDEO_RECOMMENDATIONS = "video_recommendations"


class LatencyEstimate(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CostEstimate(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
