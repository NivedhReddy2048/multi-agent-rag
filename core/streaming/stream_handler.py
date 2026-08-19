"""Streaming Response Layer enabling step-by-step incremental response rendering."""

import time
from typing import Generator, Dict, Any
from core.models.synthesis import EducationalResponse
from core.logger import get_logger

logger = get_logger("core.streaming.handler")


class ResponseStreamer:
    """Renders EducationalResponse incrementally step by step without changing underlying schema."""

    @staticmethod
    def stream_educational_response(response: EducationalResponse, delay_sec: float = 0.05) -> Generator[Dict[str, Any], None, None]:
        """Yields incremental sections of EducationalResponse for UI streaming."""
        # Step 1: Thinking / Planning
        yield {
            "step": "thinking",
            "message": "🧠 Analyzing knowledge sources & orchestrating verification...",
            "progress": 0.15,
        }
        time.sleep(delay_sec)

        # Step 2: AI Explanation
        yield {
            "step": "ai_explanation",
            "section": "AI Explanation",
            "content": response.ai_explanation,
            "progress": 0.40,
        }
        time.sleep(delay_sec)

        # Step 3: Research Papers
        if response.research:
            yield {
                "step": "research",
                "section": "Research Papers",
                "content": response.research,
                "progress": 0.60,
            }
            time.sleep(delay_sec)

        # Step 4: Books
        if response.books:
            yield {
                "step": "books",
                "section": "Textbooks & Library Books",
                "content": response.books,
                "progress": 0.75,
            }
            time.sleep(delay_sec)

        # Step 5: Videos
        if response.videos:
            yield {
                "step": "videos",
                "section": "Educational Videos",
                "content": response.videos,
                "progress": 0.85,
            }
            time.sleep(delay_sec)

        # Step 6: Learning Summary & Complete
        yield {
            "step": "completed",
            "section": "Learning Summary",
            "content": response.learning_summary or response.ai_explanation[:200],
            "full_response": response,
            "progress": 1.00,
        }
