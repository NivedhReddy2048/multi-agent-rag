"""Base class and result data structure for all agents."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from dataclasses import dataclass, field


SOURCE_MODES = frozenset({"documents", "documents+web", "web", "none"})


@dataclass
class AgentResult:
    content: str = ""
    confidence: float = 0.0
    sources: List[Dict] = field(default_factory=list)
    agent_trace: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: str = ""

    def __post_init__(self):
        """Keep the cross-agent result contract safe and backwards compatible."""
        if not isinstance(self.metadata, dict):
            self.metadata = {}
        mode = self.metadata.get("source_mode", "none")
        self.metadata["source_mode"] = mode if mode in SOURCE_MODES else "none"


class BaseAgent(ABC):
    name: str = "base"
    description: str = ""

    @abstractmethod
    def run(self, context: Dict[str, Any]) -> AgentResult:
        ...
