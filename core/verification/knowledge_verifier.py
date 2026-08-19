"""EKIP Multi-Dimensional Knowledge Verification, Cross-Source Corroboration & Evidence Ranking Engine."""

import time
import re
import uuid
import datetime
from typing import List, Dict, Any, Tuple, Optional
from difflib import SequenceMatcher

from core.models.domain import KnowledgeCollection, KnowledgeResult, SourceType
from core.models.verification import (
    VerificationProfile,
    VerifiedKnowledgeResult,
    VerifiedKnowledgeCollection,
)
from core.planner.execution_plan import ExecutionPlan
from core.verification.enhanced_crag import EnhancedCRAGVerifier
from core.logger import get_logger

logger = get_logger("core.verification.knowledge_verifier")

# Objective 4 — Base Credibility Weights
BASE_CREDIBILITY_WEIGHTS: Dict[str, float] = {
    SourceType.SEMANTIC_SCHOLAR.value: 0.95,
    SourceType.ARXIV.value: 0.90,
    SourceType.BOOK.value: 0.90,
    SourceType.GOOGLE_BOOKS.value: 0.90,
    SourceType.INTERNAL_DOCUMENT.value: 0.85,
    SourceType.WIKIPEDIA.value: 0.85,
    SourceType.GITHUB_REPO.value: 0.80,
    SourceType.TRUSTED_WEB.value: 0.75,
    SourceType.FIRE_CRAWL.value: 0.75,
    SourceType.JINA_READER.value: 0.75,
    SourceType.VIDEO.value: 0.70,
    SourceType.GENERAL_AI.value: 0.65,
}


class KnowledgeVerifier:
    """Multi-dimensional verification engine evaluating credibility, agreement, freshness, relevance, and ranking."""

    def __init__(self):
        self.crag_verifier = EnhancedCRAGVerifier()

    def _get_base_credibility(self, source_type: SourceType) -> float:
        st_val = source_type.value if hasattr(source_type, "value") else str(source_type)
        return BASE_CREDIBILITY_WEIGHTS.get(st_val, 0.70)

    def _calculate_relevance(self, query: str, res: KnowledgeResult) -> float:
        meta_stop_words = {
            "what", "where", "when", "how", "why", "this", "that", "from", "with", "have", "explain", "describe", "find",
            "recommend", "recommendation", "recommendations", "recommending", "top", "best", "good", "concept", "concepts",
            "understanding", "learn", "learning", "tutorial", "tutorials", "video", "videos", "lecture", "lectures",
            "course", "courses", "paper", "papers", "study", "notes", "summary", "overview", "show", "give", "me", "for", "about",
            "summarize", "uploaded", "file", "document", "pdf", "txt"
        }
        raw_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', query.lower()))
        q_words = raw_words - meta_stop_words
        if not q_words:
            q_words = raw_words - {"what", "where", "when", "how", "why", "this", "that", "from", "with", "have", "explain", "describe", "find"}
        if not q_words:
            return 0.85
        source_file = str(res.metadata.get("source_file", res.metadata.get("filename", res.metadata.get("document_id", ""))))
        doc_title = str(res.metadata.get("document_title", ""))
        text = f"{res.title} {res.content} {source_file} {doc_title}".lower()
        matches = sum(1 for w in q_words if w in text)
        coverage = matches / len(q_words)
        return round(max(0.0, min(1.0, coverage * 1.25)), 2)



    def _calculate_freshness(self, res: KnowledgeResult) -> float:
        pub = res.published_date or res.metadata.get("published_date") or res.metadata.get("year")
        if not pub:
            return 0.70

        try:
            pub_str = str(pub)[:4]
            year = int(pub_str)
            curr_year = datetime.datetime.now().year
            diff = curr_year - year
            if diff <= 2:
                return 1.0
            elif diff <= 5:
                return 0.85
            elif diff <= 10:
                return 0.65
            else:
                return 0.45
        except (ValueError, TypeError):
            return 0.70

    def _calculate_completeness(self, res: KnowledgeResult) -> float:
        st_val = res.source_type.value if hasattr(res.source_type, "value") else str(res.source_type)
        if st_val == SourceType.VIDEO.value or res.provider == "youtube":
            return 0.90 if (res.title and res.url) else 0.60
        text_len = len(res.content or "")
        if text_len >= 500:
            return 1.0
        elif text_len >= 200:
            return 0.80
        elif text_len >= 50:
            return 0.60
        else:
            return 0.30

    def _calculate_educational_value(self, res: KnowledgeResult) -> float:
        content = res.content.lower()
        edu_keywords = ["example", "definition", "algorithm", "step", "concept", "figure", "table", "formula", "tutorial", "overview"]
        score = 0.50
        for kw in edu_keywords:
            if kw in content:
                score += 0.08
        return round(min(1.0, score), 2)

    def _detect_duplicates(self, results: List[KnowledgeResult]) -> Tuple[List[KnowledgeResult], List[Dict[str, Any]], Dict[int, str]]:
        """Detect repeated/near-identical items and designate canonical versions."""
        duplicate_groups: List[Dict[str, Any]] = []
        item_group_map: Dict[int, str] = {}
        processed = set()

        for i in range(len(results)):
            if i in processed:
                continue
            canonical = results[i]
            group_id = f"dup_group_{i+1}"

            dups_for_i = []
            for j in range(i + 1, len(results)):
                if j in processed:
                    continue
                cand = results[j]
                sim = SequenceMatcher(None, canonical.content[:300].lower(), cand.content[:300].lower()).ratio()
                if sim >= 0.75:
                    dups_for_i.append(j)
                    processed.add(j)

            if dups_for_i:
                item_group_map[i] = group_id
                dup_titles = [results[d].title for d in dups_for_i]
                for d in dups_for_i:
                    item_group_map[d] = group_id

                duplicate_groups.append({
                    "group_id": group_id,
                    "canonical_title": canonical.title,
                    "duplicate_count": len(dups_for_i),
                    "duplicate_titles": dup_titles,
                })

        return results, duplicate_groups, item_group_map

    def _detect_conflicts_and_agreement(
        self,
        results: List[KnowledgeResult]
    ) -> Tuple[List[float], List[Dict[str, Any]]]:
        """Compute cross-source agreement scores and flag conflicting claims."""
        n = len(results)
        if n <= 1:
            return [1.0] * n, []

        agreement_scores = [0.0] * n
        conflicts: List[Dict[str, Any]] = []

        # Compare term overlaps across source pairs
        for i in range(n):
            words_i = set(re.findall(r'\b[a-zA-Z]{4,}\b', results[i].content.lower()))
            if not words_i:
                continue

            matches_sum = 0.0
            for j in range(n):
                if i == j:
                    continue
                words_j = set(re.findall(r'\b[a-zA-Z]{4,}\b', results[j].content.lower()))
                if not words_j:
                    continue

                overlap = len(words_i.intersection(words_j)) / max(1, len(words_i))
                matches_sum += overlap

                # Check for explicit negation conflict (e.g. "not", "no", "never", "opposite", "contradicts")
                negations = {"not", "no", "never", "false", "incorrect", "opposite", "disagree", "unlike"}
                i_has_neg = bool(words_i.intersection(negations))
                j_has_neg = bool(words_j.intersection(negations))

                if (i_has_neg != j_has_neg) and overlap > 0.35:
                    conflict_record = {
                        "source_a": results[i].title,
                        "source_b": results[j].title,
                        "provider_a": results[i].provider,
                        "provider_b": results[j].provider,
                        "claim_a": results[i].content[:150],
                        "claim_b": results[j].content[:150],
                        "conflict_type": "Negation or Contrasting Premise Detected",
                    }
                    if conflict_record not in conflicts:
                        conflicts.append(conflict_record)

            agreement_scores[i] = round(min(1.0, matches_sum / max(1, n - 1)), 2)

        return agreement_scores, conflicts

    def verify_collection(
        self,
        collection: KnowledgeCollection,
        plan: Optional[ExecutionPlan] = None
    ) -> VerifiedKnowledgeCollection:
        """Verify, score, cross-corroborate, and rank collected knowledge evidence."""
        t0 = time.time()
        results = collection.results

        if not results:
            logger.warning("[KnowledgeVerifier] Empty collection provided.")
            return VerifiedKnowledgeCollection(
                query=collection.query,
                execution_plan_id=collection.execution_plan_id,
                verification_timestamp=datetime.datetime.now().isoformat(),
                total_latency_ms=(time.time() - t0) * 1000,
                verification_summary="No items retrieved for verification.",
            )

        # 1. Duplicate Detection
        results, dup_groups, group_map = self._detect_duplicates(results)

        # 2. Agreement & Conflict Detection
        agreement_scores, conflicts = self._detect_conflicts_and_agreement(results)

        # 3. Enhanced CRAG Evaluation
        grade, crag_score, cat_averages, crag_notes = self.crag_verifier.evaluate_multi_source_evidence(
            collection.query, results
        )

        verified_results: List[VerifiedKnowledgeResult] = []

        for idx, res in enumerate(results):
            rel = self._calculate_relevance(collection.query, res)
            cred = self._get_base_credibility(res.source_type)
            agr = agreement_scores[idx]
            fresh = self._calculate_freshness(res)
            comp = self._calculate_completeness(res)
            edu = self._calculate_educational_value(res)

            # Multi-Dimensional Weighted Overall Score
            overall = round(
                (rel * 0.25) +
                (cred * 0.25) +
                (agr * 0.20) +
                (fresh * 0.10) +
                (comp * 0.10) +
                (edu * 0.10),
                2
            )

            profile = VerificationProfile(
                relevance_score=rel,
                credibility_score=cred,
                agreement_score=agr,
                freshness_score=fresh,
                completeness_score=comp,
                educational_value_score=edu,
                overall_score=overall,
            )

            # Explainability Notes
            notes = [
                f"Base Credibility: {cred * 100:.0f}% ({res.provider})",
                f"Query Relevance: {rel * 100:.0f}%",
                f"Cross-Source Agreement: {agr * 100:.0f}%",
                f"Freshness Score: {fresh * 100:.0f}%",
            ]
            if idx in group_map:
                notes.append(f"Grouped under duplicate group '{group_map[idx]}'")

            is_canon = idx not in group_map or group_map[idx].endswith("_1") or not any(g["group_id"] == group_map.get(idx) for g in dup_groups if g["canonical_title"] != res.title)

            # Create VerifiedKnowledgeResult
            res_dict = res.dict()
            verified_res = VerifiedKnowledgeResult(
                **res_dict,
                verification_score=overall,
                relevance_score=rel,
                credibility_score=cred,
                freshness_score=fresh,
                agreement_score=agr,
                profile=profile,
                duplicate_group=group_map.get(idx),
                verification_notes=notes,
                conflicts=[c["conflict_type"] for c in conflicts if c["source_a"] == res.title or c["source_b"] == res.title],
                is_canonical=is_canon,
            )
            verified_results.append(verified_res)

        # Objective 8 — Evidence Ranking
        verified_results.sort(key=lambda x: (x.is_canonical, x.verification_score), reverse=True)
        ranked_titles = [v.title for v in verified_results]

        avg_conf = round(sum(v.verification_score for v in verified_results) / max(1, len(verified_results)), 2)
        avg_agr = round(sum(v.agreement_score for v in verified_results) / max(1, len(verified_results)), 2)

        ver_latency = (time.time() - t0) * 1000

        summary = (
            f"Verified {len(verified_results)} evidence items. "
            f"CRAG Grade: {grade.value} (Sufficiency: {crag_score * 100:.0f}%). "
            f"Overall Agreement: {avg_agr * 100:.0f}%, Conflicts: {len(conflicts)}, Duplicates: {len(dup_groups)}."
        )

        logger.info(f"KnowledgeVerifier finished in {int(ver_latency)}ms | {summary}")

        return VerifiedKnowledgeCollection(
            query=collection.query,
            execution_plan_id=collection.execution_plan_id,
            verification_timestamp=datetime.datetime.now().isoformat(),
            total_latency_ms=ver_latency,
            verified_results=verified_results,
            conflicts=conflicts,
            duplicates=dup_groups,
            overall_confidence=avg_conf,
            overall_agreement=avg_agr,
            verification_summary=summary,
            ranking=ranked_titles,
            metadata={
                "crag_grade": grade.value,
                "crag_score": crag_score,
                "category_averages": cat_averages,
            }
        )


# Global singleton instance
knowledge_verifier = KnowledgeVerifier()
