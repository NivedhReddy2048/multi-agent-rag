"""EKIP Plugin Learning Modules Package."""

from core.workspace.modules.base_module import LearningModule
from core.workspace.modules.adaptive_engine import AdaptiveDifficultyEngine, adaptive_engine
from core.workspace.modules.flashcards import FlashcardModule
from core.workspace.modules.quiz_generator import QuizGeneratorModule
from core.workspace.modules.mind_map import MindMapModule
from core.workspace.modules.concept_graph import ConceptGraphModule
from core.workspace.modules.revision_assistant import RevisionAssistantModule
from core.workspace.modules.interview_prep import InterviewPrepModule
from core.workspace.modules.coding_practice import CodingPracticeModule
from core.workspace.modules.research_assistant import ResearchAssistantModule
from core.workspace.modules.module_manager import LearningModuleManager, module_manager

# Auto-register all core plugins into singleton module_manager
module_manager.register_module(FlashcardModule())
module_manager.register_module(QuizGeneratorModule())
module_manager.register_module(MindMapModule())
module_manager.register_module(ConceptGraphModule())
module_manager.register_module(RevisionAssistantModule())
module_manager.register_module(InterviewPrepModule())
module_manager.register_module(CodingPracticeModule())
module_manager.register_module(ResearchAssistantModule())

RevisionNotesModule = RevisionAssistantModule

__all__ = [
    "LearningModule",
    "AdaptiveDifficultyEngine",
    "adaptive_engine",
    "FlashcardModule",
    "QuizGeneratorModule",
    "MindMapModule",
    "ConceptGraphModule",
    "RevisionAssistantModule",
    "RevisionNotesModule",
    "InterviewPrepModule",
    "CodingPracticeModule",
    "ResearchAssistantModule",
    "LearningModuleManager",
    "module_manager",
]

