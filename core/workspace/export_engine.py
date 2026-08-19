"""Export Engine generating Markdown, TXT, DOCX, and HTML study materials."""

import json
from typing import Dict, Any, List, Optional
from core.models.workspace import StudyNote, Notebook, LearningSession
from core.logger import get_logger

logger = get_logger("core.workspace.export_engine")


class ExportEngine:
    """Exports study notes, notebooks, and learning sessions into Markdown, TXT, and DOCX formats."""

    def export_to_markdown(self, note: StudyNote) -> str:
        """Export StudyNote to Markdown format."""
        takeaways_txt = "\n".join([f"- {t}" for t in note.key_takeaways])
        terms_txt = "\n".join([f"- **{term}**: {defn}" for term, defn in note.important_terms.items()])

        md = f"""# {note.title}
*Query: "{note.query}"*

---

## 🧠 AI Explanation
{note.ai_explanation}

---

## 📌 Key Takeaways
{takeaways_txt if takeaways_txt else "N/A"}

---

## 📖 Important Terms
{terms_txt if terms_txt else "N/A"}
"""
        return md

    def export_notebook_to_markdown(self, notebook: Notebook) -> str:
        """Export entire Notebook with all contained notes to Markdown format."""
        md_parts = [f"# Notebook: {notebook.title}\n*{notebook.description}*\n\n---\n"]
        for idx, note in enumerate(notebook.notes, 1):
            md_parts.append(f"## {idx}. {note.title}\n")
            md_parts.append(self.export_to_markdown(note))
            md_parts.append("\n\n---\n")
        return "\n".join(md_parts)

    def export_to_txt(self, note: StudyNote) -> str:
        """Export StudyNote to Plain Text format."""
        takeaways_txt = "\n".join([f"- {t}" for t in note.key_takeaways])
        terms_txt = "\n".join([f"- {term}: {defn}" for term, defn in note.important_terms.items()])

        txt = f"""==================================================
TITLE: {note.title}
QUERY: {note.query}
==================================================

AI EXPLANATION:
{note.ai_explanation}

KEY TAKEAWAYS:
{takeaways_txt if takeaways_txt else "N/A"}

IMPORTANT TERMS:
{terms_txt if terms_txt else "N/A"}
"""
        return txt

    def export_to_docx(self, note: StudyNote) -> bytes:
        """Export StudyNote to DOCX format (returns bytes)."""
        try:
            import docx
            doc = docx.Document()
            doc.add_heading(note.title, level=1)
            p_q = doc.add_paragraph()
            r_q = p_q.add_run(f"Query: {note.query}")
            r_q.italic = True

            doc.add_heading("AI Explanation", level=2)

            doc.add_paragraph(note.ai_explanation)

            if note.key_takeaways:
                doc.add_heading("Key Takeaways", level=2)
                for kt in note.key_takeaways:
                    doc.add_paragraph(kt, style="List Bullet")

            if note.important_terms:
                doc.add_heading("Important Terms", level=2)
                for term, defn in note.important_terms.items():
                    p = doc.add_paragraph()
                    p.add_run(f"{term}: ").bold = True
                    p.add_run(defn)

            import io
            target_stream = io.BytesIO()
            doc.save(target_stream)
            return target_stream.getvalue()
        except ImportError:
            logger.warning("[ExportEngine] python-docx not installed, returning UTF-8 text bytes fallback.")
            return self.export_to_txt(note).encode("utf-8")


# Global singleton instance
export_engine = ExportEngine()
