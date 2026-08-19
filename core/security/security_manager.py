"""Security Hardening Layer providing input validation, prompt injection detection, output sanitization, and key masking."""

import re
import html
from typing import Dict, Any, Tuple
from core.logger import get_logger

logger = get_logger("core.security.manager")

# Common Prompt Injection patterns
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+previous\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+all\s+prior\s+prompts", re.IGNORECASE),
    re.compile(r"system\s+prompt\s+override", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+DAN", re.IGNORECASE),
    re.compile(r"print\s+your\s+secret\s+key", re.IGNORECASE),
]


class SecurityManager:
    """Handles enterprise security policies: injection detection, sanitization, data masking, size validation."""

    def __init__(self, max_input_characters: int = 10000):
        self.max_input_characters = max_input_characters

    def validate_and_sanitize_input(self, user_input: str) -> Tuple[bool, str, str]:
        """Validates input length, checks for prompt injection, and sanitizes text."""
        if not user_input or not user_input.strip():
            return False, "", "Input prompt cannot be empty."

        if len(user_input) > self.max_input_characters:
            return False, "", f"Input exceeds maximum allowed size of {self.max_input_characters} characters."

        # Check Prompt Injection
        for pat in INJECTION_PATTERNS:
            if pat.search(user_input):
                logger.warning(f"Security Alert: Blocked Prompt Injection attack attempt: '{user_input[:40]}...'")
                return False, "", "Security Policy Violation: Prompt injection patterns detected."

        # Sanitize HTML tags
        clean_text = html.escape(user_input.strip())
        return True, clean_text, "Valid input."

    @staticmethod
    def mask_sensitive_data(text: str) -> str:
        """Masks API keys, tokens, and authorization headers in logs or trace strings."""
        if not text:
            return ""
        # Mask API key patterns
        masked = re.sub(r"(AIzaSy[A-Za-z0-9_-]{33})", "AIzaSy*********************", text)
        masked = re.sub(r"(jina_[A-Za-z0-9_-]{40})", "jina_*********************", masked)
        masked = re.sub(r"(fc-[A-Za-z0-9_-]{32})", "fc-*********************", masked)
        masked = re.sub(r"(s2k-[A-Za-z0-9_-]{32})", "s2k-*********************", masked)
        return masked


# Global singleton instance
security_manager = SecurityManager()
