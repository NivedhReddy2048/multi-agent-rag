"""Base Provider Abstract Class & Standardized ProviderResponse Data Structure."""

import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ProviderCategory(str, Enum):
    LLM = "llm"
    SEARCH = "search"
    EXTRACTION = "extraction"
    READER = "reader"
    ACADEMIC = "academic"
    VIDEO = "video"
    BOOKS = "books"
    REPOSITORY = "repository"


class ProviderStatus(str, Enum):
    READY = "Ready (Not yet used)"
    AVAILABLE = "Available"
    CONFIGURED = "Configured"
    NOT_CONFIGURED = "Not Configured"
    ERROR = "Error"
    OFFLINE = "Offline"


class ProviderResponse(BaseModel):
    """Standardized response object for all provider operations & health checks."""

    success: bool
    provider: str
    category: ProviderCategory
    status: str
    latency_ms: float = 0.0
    error: Optional[str] = None
    data: Any = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseProvider(ABC):
    """Abstract Base Class for EKIP Knowledge Providers."""

    def __init__(self, name: str, category: ProviderCategory, is_optional: bool = True):
        self.name = name
        self.category = category
        self.is_optional = is_optional
        self.is_initialized = False
        self.last_error: Optional[str] = None
        self.last_latency_ms: float = 0.0

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize provider client/credentials."""
        pass

    @abstractmethod
    def health_check(self) -> ProviderResponse:
        """Execute diagnostic health check."""
        pass

    def search(self, query: str, **kwargs) -> ProviderResponse:
        """Execute search query if supported by provider."""
        return ProviderResponse(
            success=False,
            provider=self.name,
            category=self.category,
            status=ProviderStatus.NOT_CONFIGURED.value,
            error=f"Search operation not supported by provider '{self.name}'",
        )

    def fetch(self, identifier: str, **kwargs) -> ProviderResponse:
        """Fetch or extract document/content if supported by provider."""
        return ProviderResponse(
            success=False,
            provider=self.name,
            category=self.category,
            status=ProviderStatus.NOT_CONFIGURED.value,
            error=f"Fetch operation not supported by provider '{self.name}'",
        )

    def close(self) -> None:
        """Close connections and release resources."""
        self.is_initialized = False
