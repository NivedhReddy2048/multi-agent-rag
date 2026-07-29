"""Evidence-Driven Validation & Faithfulness Guard Agent for EKIP Platform.

Calculates evidence grounding (faithfulness = supported claims / total claims)
without relying on prompt-based string searching artifacts.
"""

import re
from typing import Dict, Any, List
from .base import BaseAgent, AgentResult, SOURCE_MODES
from core.logger import get_logger

logger = get_logger("agents.validation")


class ValidationAgent(BaseAgent):
    """Validation Agent that annotates evidence support without routing or fallbacks."""

    name = "validation"
    description = "Evaluates evidence support and claim grounding for generated responses"

    def _calculate_claim_faithfulness(self, answer: str, sources: List[Dict]) -> float:
        """Calculate evidence-based faithfulness: Supported Claims / Total Claims."""
        if not answer or not sources:
            return 0.0

        # Split response into distinct sentence claims
        raw_claims = [c.strip() for c in re.split(r'[.!?]+\s+', answer) if len(c.strip()) > 12]
        if not raw_claims:
            return 1.0

        # Build lower-cased reference text from all retrieved source chunks
        source_text = " ".join(s.get("content", "").lower() for s in sources)
        if not source_text:
            return 0.0

        supported_claims = 0
        for claim in raw_claims:
            # Extract content words (length >= 4)
            words = [w.lower() for w in re.findall(r'\b[a-zA-Z0-9]{4,}\b', claim)]
            if not words:
                supported_claims += 1
                continue

            matches = sum(1 for w in words if w in source_text)
            match_ratio = matches / len(words)

            # Claim is supported if keywords match source text or explicit citation tag exists
            if match_ratio >= 0.30 or any(tag in claim for tag in ["[SOURCE", "[DOCUMENT SOURCE", "[WEB SOURCE", "[1]", "[2]", "[3]"]):
                supported_claims += 1

        faithfulness = round(supported_claims / len(raw_claims), 2)
        return max(0.0, min(1.0, faithfulness))

    def run(self, context: Dict[str, Any]) -> AgentResult:
        answer = context.get("answer", "")
        sources = context.get("sources", [])
        query = context.get("query", "")
        source_mode = context.get("source_mode", "none")
        if source_mode not in SOURCE_MODES:
            logger.warning("Validation received invalid source mode '{}'; preserving safe none mode.", source_mode)
            source_mode = "none"

        # Validation may mark the no-answer/no-evidence condition, but must not invent
        # a fallback response or choose the next routing branch.
        if not answer.strip() and not sources:
            logger.info(f"Validation: Empty answer and no evidence for query: '{query}'")
            return AgentResult(
                content="",
                confidence=0,
                agent_trace=["🛡️ Validation: Empty answer with no evidence"],
                metadata={
                    "faithfulness": 0.0,
                    "source_mode": source_mode,
                    "warnings": ["EMPTY_ANSWER_NO_EVIDENCE"],
                },
                success=False
            )

        if not answer.strip():
            return AgentResult(
                content=answer,
                confidence=0,
                agent_trace=["🛡️ Validation: Empty synthesis output"],
                metadata={
                    "faithfulness": 0.0,
                    "source_mode": source_mode,
                    "warnings": ["EMPTY_SYNTHESIS_OUTPUT"],
                },
                success=False
            )

        # Calculate Evidence-Based Faithfulness (Supported Claims / Total Claims)
        faithfulness = self._calculate_claim_faithfulness(answer, sources)

        cited = any(f"SOURCE" in answer or f"[{i}]" in answer for i in range(1, len(sources) + 1))
        warnings = []
        if sources and not cited:
            warnings.append("CITATIONS_NOT_DETECTED")
        if source_mode == "documents+web":
            has_documents_section = "Information from Indexed Documents" in answer
            has_web_section = "Information from External Web Sources" in answer
            if not (has_documents_section and has_web_section):
                warnings.append("MIXED_EVIDENCE_SECTIONS_MISSING")

        logger.info(
            f"Validation completed for query: '{query}' | Mode: {source_mode} | "
            f"Faithfulness: {faithfulness:.2f} | Warnings: {warnings}"
        )

        return AgentResult(
            content=answer,
            confidence=0,
            agent_trace=[f"🛡️ Validation completed (Evidence Faithfulness: {faithfulness:.2f}, Mode: {source_mode})"],
            metadata={
                "faithfulness": faithfulness,
                "source_mode": source_mode,
                "citations_detected": cited,
                "warnings": warnings,
            },
            success=True
        )
