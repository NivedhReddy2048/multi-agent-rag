"""Advanced Quiz Engine Plugin Module supporting 5 question types and automatic explanations."""

from typing import Dict, Any, Optional, List
from core.workspace.modules.base_module import LearningModule
from core.workspace.modules.adaptive_engine import adaptive_engine
from core.models.synthesis import EducationalResponse
from core.models.workspace import LearningSession


class QuizGeneratorModule(LearningModule):
    """Generates advanced quizzes featuring MCQ, True/False, Multiple Select, Short Answer & Scenario questions."""

    name: str = "QuizGenerator"
    description: str = "Generates practice quiz questions across 5 question formats with automated answer explanations."
    version: str = "2.0.0"

    def process(self, response: EducationalResponse, session: Optional[LearningSession] = None) -> Dict[str, Any]:
        diff_level = adaptive_engine.estimate_difficulty(response)
        questions: List[Dict[str, Any]] = []

        # 1. MCQ Question
        if response.important_terms:
            terms = list(response.important_terms.keys())
            t1 = terms[0]
            d1 = response.important_terms[t1]
            questions.append({
                "type": "mcq",
                "difficulty": diff_level,
                "question": f"Which term matches the definition: '{d1[:100]}'?",
                "options": [t1, terms[1] if len(terms) > 1 else "Algorithm", "Model Parameter", "Hyperparameter"],
                "answer": t1,
                "explanation": f"'{t1}' is explicitly defined as: {d1}",
            })

        # 2. True / False Question
        questions.append({
            "type": "true_false",
            "difficulty": diff_level,
            "question": f"True or False: The explanation for '{response.query}' was synthesized from {len(response.providers_used)} independent knowledge sources.",
            "options": ["True", "False"],
            "answer": "True",
            "explanation": f"The response drew evidence from {', '.join(response.providers_used)}.",
        })

        # 3. Multiple Select Question
        questions.append({
            "type": "multiple_select",
            "difficulty": diff_level,
            "question": f"Which of the following are key takeaways from '{response.query}'?",
            "options": response.key_takeaways[:3] + ["Irrelevant distractor statement"],
            "correct_options": response.key_takeaways[:3],
            "explanation": "Key takeaways represent verified principles extracted during synthesis.",
        })

        # 4. Short Answer Question
        questions.append({
            "type": "short_answer",
            "difficulty": diff_level,
            "question": f"In your own words, summarize the main purpose of {response.query}.",
            "expected_keywords": [word for word in response.query.split() if len(word) > 3],
            "sample_answer": response.learning_summary or response.ai_explanation[:150],
            "explanation": f"A complete answer should highlight key concepts related to {response.query}.",
        })

        # 5. Scenario Question
        questions.append({
            "type": "scenario",
            "difficulty": diff_level,
            "question": f"Scenario: A colleague asks how to apply '{response.query}' in a production environment. What is the recommended approach?",
            "options": [
                "Follow verified step-by-step evidence guidelines",
                "Ignore evidence and use random trial-and-error",
                "Disable all verification checks",
                "Deprecate the system immediately",
            ],
            "answer": "Follow verified step-by-step evidence guidelines",
            "explanation": "Production applications should follow verified knowledge guidelines.",
        })

        return {
            "module_name": self.name,
            "difficulty_level": diff_level,
            "total_questions": len(questions),
            "quiz_questions": questions,
        }
