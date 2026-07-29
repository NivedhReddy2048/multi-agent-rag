"""Export conversations to PDF/Markdown."""

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
except ImportError:
    pass

try:
    import markdown as md
except ImportError:
    md = None

from datetime import datetime


class ConversationExporter:
    @staticmethod
    def to_markdown(messages: list, title: str = "Chat Export") -> str:
        lines = [f"# {title}\n", f"Exported: {datetime.now().isoformat()}\n"]
        for m in messages:
            role = m.get("role", "user").upper()
            lines.append(f"## {role}")
            lines.append(m.get("content", ""))
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def to_pdf(messages: list, filepath: str, title: str = "Chat Export"):
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]

        for m in messages:
            role = m.get("role", "user").upper()
            content = m.get("content", "").replace("\n", "<br/>")
            story.append(Paragraph(f"<b>{role}</b>", styles["Heading3"]))
            story.append(Paragraph(content, styles["BodyText"]))
            story.append(Spacer(1, 12))

        doc.build(story)
        return filepath
