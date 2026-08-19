"""Abstract Base Class for EKIP Plugin-Style Learning Modules."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from core.models.synthesis import EducationalResponse
from core.models.workspace import LearningSession


class LearningModule(ABC):
    """Abstract Plugin Interface for EKIP Educational Modules."""

    name: str = "BaseModule"
    description: str = "Base Learning Module Interface"
    version: str = "1.0.0"
    is_enabled: bool = True

    @abstractmethod
    def process(self, response: EducationalResponse, session: Optional[LearningSession] = None) -> Dict[str, Any]:
        """Process EducationalResponse and generate module-specific artifacts."""
        pass
