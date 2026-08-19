"""EKIP Student Workspace & Learning Package."""

from core.workspace.workspace_manager import WorkspaceManager, workspace_manager
from core.workspace.export_engine import ExportEngine, export_engine
from core.workspace.modules import (
    LearningModule,
    LearningModuleManager,
    module_manager,
    adaptive_engine,
    FlashcardModule,
    QuizGeneratorModule,
    MindMapModule,
    ConceptGraphModule,
    RevisionAssistantModule,
    RevisionNotesModule,
    InterviewPrepModule,

    CodingPracticeModule,
    ResearchAssistantModule,
)

__all__ = [
    "WorkspaceManager",
    "workspace_manager",
    "ExportEngine",
    "export_engine",
    "LearningModule",
    "LearningModuleManager",
    "module_manager",
    "adaptive_engine",
    "FlashcardModule",
    "QuizGeneratorModule",
    "MindMapModule",
    "ConceptGraphModule",
    "RevisionAssistantModule",
    "InterviewPrepModule",
    "CodingPracticeModule",
    "ResearchAssistantModule",
]
