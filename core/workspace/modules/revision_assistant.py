"""Revision Assistant Plugin Module generating one-page revision, cheat sheets, and formula sheets."""

from typing import Dict, Any, Optional, List
from core.workspace.modules.base_module import LearningModule
from core.models.synthesis import EducationalResponse
from core.models.workspace import LearningSession


class RevisionAssistantModule(LearningModule):
    """Generates subject-tailored exam cheat sheets, one-page revisions, and last-minute revision guides."""

    name: str = "RevisionAssistant"
    description: str = "Produces one-page revision sheets, exam cheat sheets, last-minute summaries, and formula reference sheets."
    version: str = "2.0.0"

    def process(self, response: EducationalResponse, session: Optional[LearningSession] = None) -> Dict[str, Any]:
        query = response.query

        # One-Page Revision
        one_page = f"""# 📄 ONE-PAGE REVISION SHEET: {query.upper()}

## 📌 Executive Summary
{response.learning_summary or response.ai_explanation[:250]}

## 🔑 Key Exam Takeaways
""" + "\n".join([f"- {kt}" for kt in response.key_takeaways]) + """

## 📖 Essential Terms & Glossary
""" + "\n".join([f"- **{t}**: {d}" for t, d in response.important_terms.items()])

        # Cheat Sheet
        cheat_sheet = f"""# ⚡ EXAM CHEAT SHEET: {query}
- Confidence: {int(response.confidence * 100)}% | Agreement: {int(response.agreement * 100)}%
""" + "\n".join([f"• {kt}" for kt in response.key_takeaways])

        # Last-Minute Revision Bullets
        last_minute = [f"⚡ {kt}" for kt in response.key_takeaways] + [f"🔑 {t}: {d[:50]}..." for t, d in response.important_terms.items()]

        # Formula / Syntax Sheet
        formulas = [
            f"Rule 1: {query} is verified across {len(response.providers_used)} independent knowledge sources.",
            f"Rule 2: High confidence evidence threshold >= {int(response.confidence * 100)}%.",
        ]

        return {
            "module_name": self.name,
            "one_page_revision": one_page,
            "cheat_sheet": cheat_sheet,
            "last_minute_revision": last_minute,
            "formula_sheet": formulas,
        }
