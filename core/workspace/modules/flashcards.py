"""Enhanced Flashcard Plugin Module supporting 6 card types and adaptive difficulty."""

from typing import Dict, Any, Optional, List
from core.workspace.modules.base_module import LearningModule
from core.workspace.modules.adaptive_engine import adaptive_engine
from core.models.synthesis import EducationalResponse
from core.models.workspace import LearningSession


class FlashcardModule(LearningModule):
    """Generates enhanced flashcards featuring 6 card types and adaptive difficulty."""

    name: str = "Flashcards"
    description: str = "Generates definition, concept, true/false, fill-in-the-blank, image placeholder, and reverse flashcards."
    version: str = "2.0.0"

    def process(self, response: EducationalResponse, session: Optional[LearningSession] = None) -> Dict[str, Any]:
        diff_str = adaptive_engine.estimate_difficulty(response)
        card_diff = adaptive_engine.map_to_card_difficulty(diff_str)

        flashcards: List[Dict[str, Any]] = []

        # 1. Definition Cards
        if response.important_terms:
            for term, defn in response.important_terms.items():
                flashcards.append({
                    "front": f"What is {term}?",
                    "back": defn,
                    "type": "definition",
                    "difficulty": card_diff,
                })

                # 6. Reverse Cards
                flashcards.append({
                    "front": f"Which term is defined as: '{defn}'?",
                    "back": term,
                    "type": "reverse_card",
                    "difficulty": card_diff,
                })

        # 2. Concept Cards
        if response.key_takeaways:
            for idx, kt in enumerate(response.key_takeaways[:2], 1):
                flashcards.append({
                    "front": f"Core Principle #{idx} regarding '{response.query}'?",
                    "back": kt,
                    "type": "concept",
                    "difficulty": card_diff,
                })

        # 3. True/False Card
        flashcards.append({
            "front": f"True or False: {response.query} is directly supported by verified knowledge evidence.",
            "back": "True. Verified confidence score is " + str(int(response.confidence * 100)) + "%.",
            "type": "true_false",
            "difficulty": card_diff,
        })

        # 4. Fill-in-the-blank Card
        if response.learning_summary:
            words = response.learning_summary.split()
            if len(words) > 4:
                target_word = words[len(words) // 2]
                blank_text = response.learning_summary.replace(target_word, "_______", 1)
                flashcards.append({
                    "front": f"Fill in the blank:\n'{blank_text}'",
                    "back": f"Missing word: {target_word}",
                    "type": "fill_in_the_blank",
                    "difficulty": card_diff,
                })

        # 5. Image Placeholder Diagram Card
        flashcards.append({
            "front": f"Visual Diagram Challenge: Draw a conceptual architecture for '{response.query}'.",
            "back": f"[Diagram Concept]: Primary flow drives synthesis across {len(response.providers_used)} sources.",
            "type": "image_placeholder",
            "difficulty": card_diff,
        })

        return {
            "module_name": self.name,
            "difficulty_level": card_diff,
            "flashcard_count": len(flashcards),
            "flashcards": flashcards,
        }
