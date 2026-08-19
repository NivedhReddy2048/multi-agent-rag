"""Revision Notes Plugin Module condensing educational response into cheat sheet format."""

from typing import Dict, Any, Optional
from core.workspace.modules.base_module import LearningModule
from core.models.synthesis import EducationalResponse
from core.models.workspace import LearningSession


class RevisionNotesModule(LearningModule):
    """Generates condensed revision cheat sheets for rapid exam preparation."""

    name: str = "RevisionNotes"
    description: str = "Condenses complex explanations into bulleted exam revision cheat sheets."

    def process(self, response: EducationalResponse, session: Optional[LearningSession] = None) -> Dict[str, Any]:
        bullets = []

        if response.learning_summary:
            bullets.append(f"Summary: {response.learning_summary}")

        if response.key_takeaways:
            bullets.extend([f"Key Takeaway: {kt}" for kt in response.key_takeaways])

        if response.important_terms:
            bullets.extend([f"Term '{t}': {d[:80]}" for t, d in response.important_terms.items()])

        return {
            "module_name": self.name,
            "revision_bullet_count": len(bullets),
            "cheat_sheet": "\n".join([f"• {b}" for b in bullets]),
        }
