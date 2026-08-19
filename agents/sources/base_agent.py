"""Abstract Base Knowledge Agent Class for Modular Retrieval Agents."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from core.models.domain import KnowledgeResult, SourceType


class BaseKnowledgeAgent(ABC):
    """Abstract interface that all EKIP modular Knowledge Source Agents must implement."""

    def __init__(self, agent_name: str, source_type: SourceType, provider_key: str):
        self.agent_name = agent_name
        self.source_type = source_type
        self.provider_key = provider_key
        self.is_initialized = False

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize provider connections, API keys, or database dependencies."""
        pass

    @abstractmethod
    def execute(self, query: str, max_results: int = 5) -> List[KnowledgeResult]:
        """Retrieve information for query and return standardized KnowledgeResult objects."""
        pass

    @abstractmethod
    def health(self) -> bool:
        """Check status and readiness of underlying knowledge provider."""
        pass

    def shutdown(self):
        """Gracefully release resources or close client connections."""
        self.is_initialized = False
