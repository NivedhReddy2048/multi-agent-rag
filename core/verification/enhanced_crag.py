"""Enhanced CRAG Verifier for Multi-Source Educational Evidence Verification."""

import re
from enum import Enum
from typing import List, Dict, Any, Tuple
from core.models.domain import KnowledgeResult, SourceType
from core.logger import get_logger

logger = get_logger("core.verification.enhanced_crag")


class EvidenceQualityGrade(str, Enum):
    CORRECT = "CORRECT"        # High confidence, sufficient evidence
    AMBIGUOUS = "AMBIGUOUS"    # Partial evidence, potential gaps/conflicts
    INCORRECT = "INCORRECT"    # Low coverage, insufficient evidence


class EnhancedCRAGVerifier:
    """Evaluates multi-source evidence sufficiency across Documents, Wikipedia, Research, Web, Books, and Videos."""

    def evaluate_multi_source_evidence(
        self,
        query: str,
        results: List[KnowledgeResult]
    ) -> Tuple[EvidenceQualityGrade, float, Dict[str, float], List[str]]:
        """Evaluate evidence quality grade across all retrieved multi-source KnowledgeResult items."""
        if not results:
            logger.info("EnhancedCRAG: 0 results provided for evaluation.")
            return EvidenceQualityGrade.INCORRECT, 0.0, {}, ["No knowledge sources returned evidence."]

        q_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())) - {
            "what", "where", "when", "how", "why", "this", "that", "from", "with", "have", "explain", "describe", "find"
        }

        category_scores: Dict[str, List[float]] = {}
        trace_notes: List[str] = []

        for res in results:
            st_key = res.source_type.value if hasattr(res.source_type, "value") else str(res.source_type)
            content_text = f"{res.title} {res.content}".lower()

            if not q_words:
                match_score = 0.8
            else:
                matches = sum(1 for w in q_words if w in content_text)
                match_score = matches / len(q_words)

            len_score = min(1.0, len(res.content) / 800)
            item_score = (match_score * 0.7) + (len_score * 0.3)

            if st_key not in category_scores:
                category_scores[st_key] = []
            category_scores[st_key].append(item_score)

        # Category average score
        cat_averages: Dict[str, float] = {
            cat: round(sum(scores) / len(scores), 2)
            for cat, scores in category_scores.items()
        }

        # Overall weighted multi-source score
        overall_score = round(sum(cat_averages.values()) / len(cat_averages), 2) if cat_averages else 0.0

        if overall_score >= 0.70:
            grade = EvidenceQualityGrade.CORRECT
            trace_notes.append(f"✅ Enhanced CRAG: High multi-source evidence quality (Grade: CORRECT, Score: {overall_score})")
        elif overall_score >= 0.35:
            grade = EvidenceQualityGrade.AMBIGUOUS
            trace_notes.append(f"⚠️ Enhanced CRAG: Partial evidence quality (Grade: AMBIGUOUS, Score: {overall_score})")
        else:
            grade = EvidenceQualityGrade.INCORRECT
            trace_notes.append(f"❌ Enhanced CRAG: Insufficient multi-source evidence (Grade: INCORRECT, Score: {overall_score})")

        for cat, avg in cat_averages.items():
            trace_notes.append(f" - [{cat.upper()}] Evidence Sufficiency: {avg * 100:.0f}%")

        return grade, overall_score, cat_averages, trace_notes
