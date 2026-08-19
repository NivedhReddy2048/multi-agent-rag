"""Domain Models for EKIP Phase 2.6 Student Workspace, Learning Sessions & Knowledge Library."""

import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Bookmark(BaseModel):
    """Resource bookmark item (paper, book, video, article, GitHub repo)."""

    id: str = Field(default="")
    title: str = Field(default="")
    resource_type: str = Field(default="article", description="paper | book | video | repo | article")
    url: Optional[str] = Field(default="")
    is_read: bool = Field(default=False)
    created_at: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StudyNote(BaseModel):
    """Saved educational response or user study note."""

    id: str = Field(default="")
    session_id: Optional[str] = Field(default="")
    notebook_id: Optional[str] = Field(default="")
    query: str = Field(default="")
    title: str = Field(default="")
    ai_explanation: str = Field(default="")
    key_takeaways: List[str] = Field(default_factory=list)
    important_terms: Dict[str, str] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)


class Notebook(BaseModel):
    """Subject notebook for organizing study notes."""

    id: str = Field(default="")
    title: str = Field(default="")
    description: str = Field(default="")
    notes: List[StudyNote] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)


class StudyCollection(BaseModel):
    """Grouped collection of reusable learning resources."""

    id: str = Field(default="")
    title: str = Field(default="")
    category: str = Field(default="general")
    items: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)


class LearningSession(BaseModel):
    """Persistent student learning session."""

    id: str = Field(default="")
    title: str = Field(default="")
    description: str = Field(default="")
    topics: List[str] = Field(default_factory=list)
    query_count: int = Field(default=0)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class WorkspaceProgress(BaseModel):
    """Student learning progress metrics."""

    total_queries: int = Field(default=0)
    total_sessions: int = Field(default=0)
    saved_notes_count: int = Field(default=0)
    notebooks_count: int = Field(default=0)
    bookmarks_count: int = Field(default=0)
    read_bookmarks_count: int = Field(default=0)
    collections_count: int = Field(default=0)
    topics_explored: List[str] = Field(default_factory=list)
