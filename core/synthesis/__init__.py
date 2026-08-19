"""EKIP Knowledge Synthesis, Educational Response Composition & Guided Learning Package."""

from core.synthesis.knowledge_synthesizer import KnowledgeSynthesizer, knowledge_synthesizer
from core.synthesis.prompt_builder import EducationalPromptBuilder
from core.synthesis.response_composer import ResponseComposer, response_composer
from core.synthesis.guided_learning import GuidedLearningEngine, guided_learning_engine

__all__ = [
    "KnowledgeSynthesizer",
    "knowledge_synthesizer",
    "EducationalPromptBuilder",
    "ResponseComposer",
    "response_composer",
    "GuidedLearningEngine",
    "guided_learning_engine",
]
