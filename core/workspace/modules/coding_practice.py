"""Coding Practice Plugin Module generating programming challenges, hints, solutions, and complexity analysis."""

from typing import Dict, Any, Optional, List
from core.workspace.modules.base_module import LearningModule
from core.models.synthesis import EducationalResponse
from core.models.workspace import LearningSession


class CodingPracticeModule(LearningModule):
    """Generates hands-on coding exercises, hints, reference solutions, edge cases, and time/space complexity analysis."""

    name: str = "CodingPractice"
    description: str = "Generates programming challenges, test edge cases, sample Python solutions, and algorithmic complexity discussions."
    version: str = "1.0.0"

    def process(self, response: EducationalResponse, session: Optional[LearningSession] = None) -> Dict[str, Any]:
        topic = response.query

        challenges = [
            {
                "title": f"Implement {topic} Core Functionality in Python",
                "problem_statement": f"Write a clean Python class or function that models the core behavior of '{topic}'.",
                "hints": [
                    "Start by defining input data structures.",
                    "Use modular functions with type annotations.",
                ],
                "sample_solution": f"def solve_{topic.lower().replace(' ', '_')}(inputs: list) -> dict:\n    # Implementation of {topic}\n    return {{'result': 'success', 'count': len(inputs)}}\n",
                "edge_cases": [
                    "Empty input list `[]`",
                    "Invalid input data types",
                    "High concurrency execution",
                ],
                "time_complexity": "O(N) where N is number of elements",
                "space_complexity": "O(1) auxiliary space",
            }
        ]

        return {
            "module_name": self.name,
            "topic": topic,
            "challenges_count": len(challenges),
            "coding_challenges": challenges,
        }
