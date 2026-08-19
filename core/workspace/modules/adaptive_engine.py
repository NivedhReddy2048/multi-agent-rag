"""Adaptive Difficulty Engine for tailoring Learning Module outputs to learner profile."""

from typing import Dict, Any, Optional
from core.models.synthesis import EducationalResponse
from core.logger import get_logger

logger = get_logger("core.workspace.modules.adaptive_engine")


class AdaptiveDifficultyEngine:
    """Estimates learner's knowledge level and computes target difficulty for learning modules."""

    def estimate_difficulty(self, response: EducationalResponse, workspace_history_count: int = 0) -> str:
        """Determines target difficulty ('beginner', 'intermediate', 'advanced' / 'easy', 'medium', 'hard')."""
        mode = response.educational_mode.lower()

        if "beginner" in mode or "simple" in mode or workspace_history_count < 2:
            return "beginner"
        elif "advanced" in mode or "academic" in mode or workspace_history_count > 10:
            return "advanced"
        return "intermediate"

    def map_to_card_difficulty(self, difficulty: str) -> str:
        mapping = {"beginner": "easy", "intermediate": "medium", "advanced": "hard"}
        return mapping.get(difficulty, "medium")


adaptive_engine = AdaptiveDifficultyEngine()
