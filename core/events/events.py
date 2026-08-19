"""Event definitions for EKIP Internal Event Bus."""

import time
import uuid
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class Event(BaseModel):
    """Base class for all system events."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    event_type: str
    timestamp: float = Field(default_factory=time.time)
    payload: Dict[str, Any] = Field(default_factory=dict)


class EducationalResponseCreated(Event):
    event_type: str = "EducationalResponseCreated"


class KnowledgeCollectionCompleted(Event):
    event_type: str = "KnowledgeCollectionCompleted"


class VerificationCompleted(Event):
    event_type: str = "VerificationCompleted"


class WorkspaceSaved(Event):
    event_type: str = "WorkspaceSaved"


class NotebookExported(Event):
    event_type: str = "NotebookExported"


class LearningModuleCompleted(Event):
    event_type: str = "LearningModuleCompleted"


class CacheHit(Event):
    event_type: str = "CacheHit"


class CacheMiss(Event):
    event_type: str = "CacheMiss"


class ProviderFailure(Event):
    event_type: str = "ProviderFailure"


class BackgroundJobCompleted(Event):
    event_type: str = "BackgroundJobCompleted"
