"""Interview Preparation Plugin Module generating interview questions, answers, and evaluation rubrics."""

from typing import Dict, Any, Optional, List
from core.workspace.modules.base_module import LearningModule
from core.models.synthesis import EducationalResponse
from core.models.workspace import LearningSession


class InterviewPrepModule(LearningModule):
    """Generates CS & Tech interview questions, expected answers, follow-up probes, and evaluation rubrics."""

    name: str = "InterviewPrep"
    description: str = "Generates technical interview questions, sample answer keys, deep-dive follow-ups, and grading rubrics."
    version: str = "1.0.0"

    def process(self, response: EducationalResponse, session: Optional[LearningSession] = None) -> Dict[str, Any]:
        topic = response.query

        common_qs = [
            {
                "question": f"Can you explain {topic} and its primary real-world use cases?",
                "expected_answer": response.learning_summary or response.ai_explanation[:200],
                "follow_up": f"What are the main limitations or trade-offs when implementing {topic}?",
            },
        ]

        advanced_qs = [
            {
                "question": f"How does {topic} perform under high scale or adversarial conditions?",
                "expected_answer": f"Under scale, {topic} requires strict evidence verification and multi-provider failover strategy.",
                "follow_up": "How would you optimize latency in this pipeline?",
            },
        ]

        rubric = {
            "Strong Answer (5/5)": f"Clear conceptual explanation of {topic}, cites key takeaways, mentions trade-offs.",
            "Adequate Answer (3/5)": f"Basic explanation of {topic} without deep architectural details.",
            "Weak Answer (1/5)": f"Confuses {topic} with unrelated concepts or displays hallucinated claims.",
        }

        return {
            "module_name": self.name,
            "topic": topic,
            "common_questions": common_qs,
            "advanced_questions": advanced_qs,
            "evaluation_rubric": rubric,
        }
