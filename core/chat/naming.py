"""Chat title generator module for EKIP Chat System."""

import re


def generate_chat_title(first_message: str, max_length: int = 40) -> str:
    """Generate a concise, meaningful title from the user's first message.

    Rules:
    1. If message is a question, strip trailing question mark and truncate.
    2. If message mentions a document name (e.g. filename.pdf), use that.
    3. Take first 3-5 significant words.
    4. Cap at max_length characters with ellipsis if needed.
    5. Always return a non-empty string.
    """
    msg = (first_message or "").strip()
    if not msg:
        return "New Chat"

    # Check for document filename pattern (e.g. Deep_Solar_System_Report.pdf)
    doc_match = re.search(r'([\w\-\_]+\.(?:pdf|docx|txt|md|csv|png|jpg))', msg, re.IGNORECASE)
    if doc_match:
        raw_doc = doc_match.group(1)
        doc_stem = raw_doc.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
        if "summarize" in msg.lower():
            title = f"Summarize {doc_stem}"
        else:
            title = f"Doc: {doc_stem}"
        if len(title) <= max_length:
            return title
        return title[: max_length - 3].strip() + "..."

    # Strip question mark
    msg = msg.rstrip("?")

    if len(msg) <= max_length:
        return msg

    # Split on sentence delimiters
    for delim in [". ", "! ", "; ", " - ", " — "]:
        if delim in msg:
            candidate = msg.split(delim)[0]
            if 10 <= len(candidate) <= max_length:
                return candidate

    # Word-based truncation with ellipsis
    words = msg.split()
    title = ""
    for word in words:
        if len(title) + len(word) + 1 > max_length - 3:
            break
        title = f"{title} {word}" if title else word

    return title.strip() + "..." if title else "New Chat"
