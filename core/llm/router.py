"""Intelligent Provider Router for EKIP Multi-LLM Layer."""

from typing import List, Optional, Dict, Any
from .base_provider import BaseLLMProvider
from .provider_registry import ProviderRegistry
from core.logger import get_logger

logger = get_logger("core.llm.router")


class IntelligentRouter:
    """Selects optimal provider based on task intent and real-time circuit health."""

    ROUTING_PREFERENCES: Dict[str, List[str]] = {
        "general_chat": ["groq", "gemini", "cohere", "mistral"],
        "document_qa": ["gemini", "groq", "cohere", "mistral"],
        "executive_reports": ["gemini", "groq", "cohere", "mistral"],
        "long_summaries": ["cohere", "gemini", "groq", "mistral"],
        "code_questions": ["mistral", "groq", "gemini", "cohere"],
        "QA": ["gemini", "groq", "cohere", "mistral"],
        "SUMMARY": ["gemini", "groq", "cohere", "mistral"],
        "REPORT": ["gemini", "groq", "cohere", "mistral"],
        "COMPARE": ["gemini", "groq", "cohere", "mistral"],
        "default": ["gemini", "groq", "cohere", "mistral"],
    }

    def __init__(self, registry: ProviderRegistry):
        self.registry = registry

    def determine_intent(self, prompt_or_inputs: Any, explicit_intent: Optional[str] = None) -> str:
        """Infer task intent from explicit parameter, dictionary inputs, or prompt keywords."""
        if explicit_intent:
            norm = str(explicit_intent).strip().upper()
            if norm in self.ROUTING_PREFERENCES:
                return norm
            lower = str(explicit_intent).strip().lower()
            if lower in self.ROUTING_PREFERENCES:
                return lower

        text = ""
        if isinstance(prompt_or_inputs, dict):
            text = str(prompt_or_inputs.get("query", prompt_or_inputs.get("question", prompt_or_inputs.get("text", "")))).lower()
            if "intent" in prompt_or_inputs and prompt_or_inputs["intent"] in self.ROUTING_PREFERENCES:
                return prompt_or_inputs["intent"]
        elif isinstance(prompt_or_inputs, str):
            text = prompt_or_inputs.lower()

        # Keyword heuristics
        if any(kw in text for kw in ["code", "python", "script", "function", "bug", "sql", "def ", "class "]):
            return "code_questions"
        elif any(kw in text for kw in ["summary", "summarize", "executive summary", "overview", "long"]):
            return "long_summaries"
        elif any(kw in text for kw in ["report", "analysis", "audit", "briefing"]):
            return "executive_reports"
        elif any(kw in text for kw in ["document", "pdf", "file", "page", "section", "according to"]):
            return "document_qa"
        elif any(kw in text for kw in ["hi", "hello", "who are you", "chat", "how are you"]):
            return "general_chat"

        return "default"

    def select_ordered_providers(self, intent: str = "default") -> List[BaseLLMProvider]:
        """
        Return provider instances ordered by intent preference,
        filtering out providers with OPEN circuits.
        """
        preferred_names = self.ROUTING_PREFERENCES.get(intent, self.ROUTING_PREFERENCES["default"])
        
        ordered = []
        skipped = []

        for name in preferred_names:
            provider = self.registry.get_provider(name)
            if not provider:
                continue

            if provider.is_circuit_open():
                skipped.append(f"{name} (Circuit OPEN)")
                continue

            ordered.append(provider)

        logger.info(f"Intelligent Router [Intent: {intent}] -> Selected: {[p.name for p in ordered]} | Skipped: {skipped}")
        return ordered
