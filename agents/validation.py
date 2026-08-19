"""Evidence-Driven Validation & Deterministic Claim-Level Grounding Guard for EKIP Platform.

Evaluates evidence support, citation correctness, and claim grounding for generated responses
using deterministic, source-aware claim-to-chunk verification.
"""

import re
from typing import Dict, Any, List, Tuple, Optional, Set
from .base import BaseAgent, AgentResult, SOURCE_MODES
from core.logger import get_logger

logger = get_logger("agents.validation")


class ValidationAgent(BaseAgent):
    """Validation Agent that annotates evidence support and claim-level grounding without routing or fallbacks."""

    name = "validation"
    description = "Evaluates evidence support, citation correctness, and claim grounding for generated responses"

    def __init__(self, config=None, evaluator=None):
        self.config = config
        from core.validation.entailment_evaluator import EntailmentEvaluator
        self.entailment_evaluator = evaluator or EntailmentEvaluator()

    def _extract_claims_and_structure(self, answer: str) -> List[Dict[str, Any]]:
        """Segment answer into evaluable claims, excluding Markdown headings, code blocks, and boilerplate. Supports citation-aware clause extraction."""
        if not answer:
            return []

        # 1. Remove fenced code blocks
        clean_text = re.sub(r'```[\s\S]*?```', '', answer)

        # 2. Remove horizontal rules
        clean_text = re.sub(r'^\s*[-*_]{3,}\s*$', '', clean_text, flags=re.MULTILINE)

        lines = clean_text.split('\n')
        extracted: List[Dict[str, Any]] = []

        disclaimer_patterns = [
            r"\bdoes not (contain|mention|provide|include|specify)\b",
            r"\bnot (mentioned|provided|specified|included|present) in\b",
            r"\bunsupported (by|in) the (document|evidence|source)\b",
            r"\bmissing from (the|your) (document|file|uploaded)\b",
            r"\bno information (available|found|provided)\b",
            r"\bcouldn't find (enough|relevant) information\b",
            r"\bunsupported information\b",
        ]

        framework_boilerplate_patterns = [
            r"^\s*#+\s+",                                      # Markdown headings (# Title)
            r"^\s*\*\*[^*]+\*\*\s*$",                          # Bold heading standalone line
            r"below is a (complete|runnable|detailed|step-by-step)",
            r"in this (lesson|walkthrough|guide|overview|section)",
            r"let us (explore|examine|look at|understand)",
            r"to better understand this concept",
            r"in deep learning|in machine learning|in natural language processing",
            r"this concludes the overview|summary of key points|final thoughts",
            r"question \d+",
            r"^[a-d]\)\s+",                                 # Quiz options: A) Option
        ]

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            is_heading = bool(re.match(r'^\s*#+\s+', line_str)) or bool(re.match(r'^\s*\*\*[^*]+\*\*\s*$', line_str))

            sentence_fragments = [
                s.strip() for s in re.split(r'\.\s+|[!?]+\s+', line_str)
                if len(s.strip()) > 0
            ]

            for frag in sentence_fragments:
                frag_clean = re.sub(r'^\s*[-*•\d+.]+\s*', '', frag).strip()
                if len(frag_clean) < 10:
                    continue

                frag_lower = frag_clean.lower()
                is_disclaimer = any(re.search(pat, frag_lower) for pat in disclaimer_patterns)
                is_boilerplate = is_heading or any(re.search(pat, frag_lower) for pat in framework_boilerplate_patterns)

                raw_citations = re.findall(r'\[(\d+)\]', frag_clean)
                citation_ids = [int(c) for c in raw_citations]

                if frag_clean.lower().startswith("**answer**"):
                    frag_clean = re.sub(r'^\*\*answer\*\*:\s*', '', frag_clean, flags=re.IGNORECASE).strip()
                    is_boilerplate = False

                is_applicable = is_disclaimer or bool(citation_ids) or not is_boilerplate

                # Citation-Aware Clause Extraction for compound multi-citation sentences e.g. "BERT uses encoders [1] and is trained on MLM [2]."
                clause_matches = list(re.finditer(r'([^\[\]]+?)\s*(\[\d+\](?:\s*\[\d+\])*)', frag_clean))
                if len(clause_matches) > 1:
                    for idx, m in enumerate(clause_matches):
                        clause_text = m.group(1).strip()
                        # Trim leading clause conjunctions e.g. "and is trained..." -> "is trained..."
                        clause_clean = re.sub(r'^(and|but|while|whereas|also|or)\s+', '', clause_text, flags=re.IGNORECASE).strip()
                        if len(clause_clean) < 5:
                            clause_clean = clause_text
                        c_raw_cids = re.findall(r'\[(\d+)\]', m.group(2))
                        cids = [int(c) for c in c_raw_cids]
                        extracted.append({
                            "text": clause_clean,
                            "citations": cids,
                            "is_disclaimer": is_disclaimer,
                            "is_applicable": is_applicable,
                            "original_sentence": frag_clean,
                            "clause_index": idx,
                        })
                else:
                    extracted.append({
                        "text": frag_clean,
                        "citations": citation_ids,
                        "is_disclaimer": is_disclaimer,
                        "is_applicable": is_applicable,
                        "original_sentence": frag_clean,
                        "clause_index": 0,
                    })

        return extracted

    def _verify_strict_numeric_grounding(self, claim: str, source_text: str, combined_cited_text: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Phase 10B Strict Numeric Grounding Guard:
        Return ("CONTRADICTED", meta) if claim contradicts source numbers.
        Return ("UNSUPPORTED", meta) if specific quantitative assertion in claim is completely absent from cited evidence.
        Return ("SUPPORTED_NUMERIC", meta) if numbers present and supported.
        Return ("NO_NUMERIC_CLAIMS", meta) if no specific numbers in claim.
        """
        claim_clean = re.sub(r'\[\d+\]', '', claim).lower()
        # Normalize percent words e.g. "12 percent" -> "12%"
        claim_clean = re.sub(r'(\d+)\s*percent', r'\1%', claim_clean)
        src_lower = source_text.lower()
        src_lower = re.sub(r'(\d+)\s*percent', r'\1%', src_lower)
        all_cited_lower = (combined_cited_text or source_text).lower()
        all_cited_lower = re.sub(r'(\d+)\s*percent', r'\1%', all_cited_lower)

        # 1. Quantity pattern check e.g. "12 attention heads" vs "8 attention heads" or "92%" vs "82%"
        qty_patterns = [
            (r'(\d+)\s*(attention heads|heads)', 'attention heads'),
            (r'(\d+)\s*(layers|blocks)', 'layers'),
            (r'(\d+)\s*(embedding dimension|dimension)', 'dimension'),
            (r'(\d+)\s*(parameters|bits)', 'parameters'),
            (r'(\d+%|\d+\.\d+%)', 'percentage'),
            (r'\b([12]\d{3})\b', 'year'),
        ]

        # Check for explicit contradiction
        for pat, entity in qty_patterns:
            claim_match = re.search(pat, claim_clean)
            if claim_match:
                claim_val = claim_match.group(1)
                src_match = re.search(pat, src_lower)
                if src_match:
                    src_val = src_match.group(1)
                    if claim_val != src_val:
                        return "CONTRADICTED", {"entity": entity, "claim_val": claim_val, "src_val": src_val}

        # Check for missing numeric evidence (Test 3: claim asserted "12 attention heads", source has "multi-head attention")
        claim_nums = set(re.findall(r'\b\d+(?:\.\d+)?%?\b', claim_clean))
        src_nums = set(re.findall(r'\b\d+(?:\.\d+)?%?\b', all_cited_lower))

        # Filter out trivial numbers e.g. "1" from indexing
        claim_nums = {n for n in claim_nums if n != "1"}
        src_nums = {n for n in src_nums if n != "1"}

        if claim_nums:
            missing_nums = claim_nums - src_nums
            if missing_nums:
                # If claim has a specific numeric detail absent from cited evidence
                return "UNSUPPORTED", {
                    "numeric_claim_values": list(claim_nums),
                    "numeric_source_values": list(src_nums),
                    "missing_numbers": list(missing_nums),
                    "reason": "specific_numeric_detail_absent_from_evidence"
                }

            return "SUPPORTED_NUMERIC", {
                "numeric_claim_values": list(claim_nums),
                "numeric_source_values": list(src_nums),
                "numeric_grounded": True
            }

        return "NO_NUMERIC_CLAIMS", {}

    def _verify_numeric_and_negation_consistency(self, claim: str, source_text: str, combined_cited_text: Optional[str] = None) -> bool:
        """Return True if claim contradicts source on numbers or negations, else False."""
        claim_clean = re.sub(r'\[\d+\]', '', claim).lower()
        src_lower = source_text.lower()
        all_cited_lower = (combined_cited_text or source_text).lower()

        qty_status, _ = self._verify_strict_numeric_grounding(claim, source_text, combined_cited_text=combined_cited_text)
        if qty_status == "CONTRADICTED":
            return True

        negations = {"not", "no", "never", "without", "lacks", "neither"}
        claim_words = set(re.findall(r'\b[a-z]{3,}\b', claim_clean))
        src_words = set(re.findall(r'\b[a-z]{3,}\b', src_lower))
        claim_has_neg = bool(claim_words.intersection(negations))
        src_has_neg = bool(src_words.intersection(negations))

        overlap = len(claim_words.intersection(src_words)) / max(1, len(claim_words))
        if (claim_has_neg != src_has_neg) and overlap >= 0.40:
            logger.debug(f"[Validation Grounding] Negation contradiction detected (Claim neg={claim_has_neg}, Source neg={src_has_neg})")
            return True

        return False

    def _evaluate_claim_against_sources(self, claim_obj: Dict[str, Any], sources: List[Dict[str, Any]]) -> str:
        """Evaluate a single claim against cited source(s) or global sources using Phase 10B deterministic decision precedence."""
        claim_text = claim_obj["text"]
        citation_ids = claim_obj["citations"]
        is_disclaimer = claim_obj["is_disclaimer"]

        if is_disclaimer:
            return "SUPPORTED"

        num_sources = len(sources)

        if citation_ids:
            valid_cids = [c for c in citation_ids if 1 <= c <= num_sources]
            combined_cited_text = " ".join(
                (sources[c - 1].get("content") or sources[c - 1].get("snippet") or "").strip()
                for c in valid_cids
            )

            source_statuses = []
            for cid in citation_ids:
                if cid < 1 or cid > num_sources:
                    source_statuses.append("INVALID_CITATION_INDEX")
                    continue

                src = sources[cid - 1]
                src_content = (src.get("content") or src.get("snippet") or "").strip()

                if not src_content:
                    source_statuses.append("UNSUPPORTED")
                    continue

                # 1. Hard Guard: Strict Numeric Grounding
                num_status, num_meta = self._verify_strict_numeric_grounding(claim_text, src_content, combined_cited_text=combined_cited_text)
                if num_status == "CONTRADICTED":
                    source_statuses.append("CONTRADICTED")
                    continue
                elif num_status == "UNSUPPORTED":
                    source_statuses.append("UNSUPPORTED")
                    continue

                # 2. Hard Guard: Negation Mismatch
                if self._verify_numeric_and_negation_consistency(claim_text, src_content, combined_cited_text=combined_cited_text):
                    source_statuses.append("CONTRADICTED")
                    continue

                # 3. Semantic Entailment Evaluation (NLI with Heuristic Fallback)
                eval_res = self.entailment_evaluator.evaluate(claim_text, src_content)
                if eval_res.evaluator_mode == "nli":
                    if eval_res.label == "ENTAILED":
                        source_statuses.append("SUPPORTED")
                    elif eval_res.label == "CONTRADICTED":
                        source_statuses.append("CONTRADICTED")
                    else:
                        source_statuses.append("UNSUPPORTED")
                else:
                    # Heuristic Fallback (Lexical Overlap)
                    stopwords = {"this", "that", "with", "from", "have", "explain", "concept", "system", "model", "architecture", "using", "which", "where", "what", "how", "features", "contains", "ekip"}
                    words = [w.lower() for w in re.findall(r'\b[a-zA-Z0-9]{4,}\b', claim_text) if w.lower() not in stopwords]

                    if not words:
                        source_statuses.append("UNSUPPORTED")
                        continue

                    src_lower = src_content.lower()
                    matches = sum(1 for w in words if w in src_lower)
                    match_ratio = matches / len(words)

                    if match_ratio >= 0.35:
                        source_statuses.append("SUPPORTED")
                    elif match_ratio >= 0.20:
                        source_statuses.append("PARTIALLY_SUPPORTED")
                    else:
                        source_statuses.append("UNSUPPORTED")

            # Deterministic Aggregation across multiple citations e.g. [1][2]
            if any(s == "INVALID_CITATION_INDEX" for s in source_statuses):
                return "INVALID_CITATION"
            if any(s == "CONTRADICTED" for s in source_statuses):
                return "CONTRADICTED"
            if all(s == "SUPPORTED" for s in source_statuses):
                return "SUPPORTED"
            if any(s in ("SUPPORTED", "PARTIALLY_SUPPORTED") for s in source_statuses):
                return "PARTIALLY_SUPPORTED"
            return "UNSUPPORTED"

        else:
            # Uncited claim in document-grounded evaluation
            all_source_text = " ".join((s.get("content") or s.get("snippet") or "").lower() for s in sources)
            stopwords = {"this", "that", "with", "from", "have", "explain", "concept", "system", "model", "architecture", "using", "which"}
            words = [w.lower() for w in re.findall(r'\b[a-zA-Z0-9]{4,}\b', claim_text) if w.lower() not in stopwords]

            if not words or not all_source_text:
                return "UNSUPPORTED"

            matches = sum(1 for w in words if w in all_source_text)
            match_ratio = matches / len(words)

            if match_ratio >= 0.40:
                return "SUPPORTED"
            elif match_ratio >= 0.20:
                return "PARTIALLY_SUPPORTED"
            return "NO_CITATION"

    def run(self, context: Dict[str, Any]) -> AgentResult:
        answer = context.get("answer", "")
        sources = context.get("sources", [])
        query = context.get("query", "")
        source_mode = context.get("source_mode", "none")
        source_strategy = str(context.get("source_strategy", "")).lower()

        if source_mode not in SOURCE_MODES:
            logger.warning("Validation received invalid source mode '{}'; preserving safe none mode.", source_mode)
            source_mode = "none"

        is_general_knowledge = (source_strategy == "general_knowledge" or source_mode == "general_knowledge")

        if not answer.strip() and not sources:
            logger.info(f"Validation: Empty answer and no evidence for query: '{query}'")
            return AgentResult(
                content="",
                confidence=0,
                agent_trace=["🛡️ Validation: Empty answer with no evidence"],
                metadata={
                    "faithfulness": None if is_general_knowledge else 0.0,
                    "faithfulness_applicable": not is_general_knowledge,
                    "faithfulness_reason": "general_knowledge_no_document_grounding_required" if is_general_knowledge else "empty_retrieval_insufficient_evidence",
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
                    "faithfulness": None if is_general_knowledge else 0.0,
                    "faithfulness_applicable": not is_general_knowledge,
                    "faithfulness_reason": "general_knowledge_no_document_grounding_required" if is_general_knowledge else "empty_synthesis_output",
                    "source_mode": source_mode,
                    "warnings": ["EMPTY_SYNTHESIS_OUTPUT"],
                },
                success=False
            )

        warnings = []

        if is_general_knowledge:
            faithfulness = None
            faithfulness_applicable = False
            faithfulness_reason = "general_knowledge_no_document_grounding_required"
            cited = False
            citations_applicable = False
            telemetry = {
                "claims_total": 0,
                "claims_applicable": 0,
                "claims_grounded": 0,
                "claims_partially_supported": 0,
                "claims_unsupported": 0,
                "claims_contradicted": 0,
                "claims_invalid_citation": 0,
                "claims_no_citation": 0,
                "citations_total": 0,
                "citations_valid": 0,
                "citations_invalid": 0,
                "attribution_valid": True,
            }
        else:
            faithfulness_applicable = True
            citations_applicable = bool(sources)

            if not sources:
                faithfulness = 0.0
                faithfulness_reason = "empty_retrieval_insufficient_evidence"
                cited = False
                telemetry = {
                    "claims_total": 0,
                    "claims_applicable": 0,
                    "claims_grounded": 0,
                    "claims_partially_supported": 0,
                    "claims_unsupported": 0,
                    "claims_contradicted": 0,
                    "claims_invalid_citation": 0,
                    "claims_no_citation": 0,
                    "citations_total": 0,
                    "citations_valid": 0,
                    "citations_invalid": 0,
                    "attribution_valid": False,
                }
            else:
                extracted_claims = self._extract_claims_and_structure(answer)
                applicable_claims = [c for c in extracted_claims if c["is_applicable"]]

                claims_grounded = 0
                claims_partially_supported = 0
                claims_unsupported = 0
                claims_contradicted = 0
                claims_invalid_citation = 0
                claims_no_citation = 0

                citations_total = 0
                citations_valid = 0
                citations_invalid = 0

                num_sources = len(sources)

                for claim_obj in applicable_claims:
                    cids = claim_obj["citations"]
                    citations_total += len(cids)
                    for cid in cids:
                        if 1 <= cid <= num_sources:
                            citations_valid += 1
                        else:
                            citations_invalid += 1

                    verdict = self._evaluate_claim_against_sources(claim_obj, sources)
                    if verdict == "SUPPORTED":
                        claims_grounded += 1
                    elif verdict == "PARTIALLY_SUPPORTED":
                        claims_partially_supported += 1
                    elif verdict == "CONTRADICTED":
                        claims_contradicted += 1
                    elif verdict == "INVALID_CITATION":
                        claims_invalid_citation += 1
                    elif verdict == "NO_CITATION":
                        claims_no_citation += 1
                    else:
                        claims_unsupported += 1

                claims_applicable_count = len(applicable_claims)
                if claims_applicable_count == 0:
                    faithfulness = 1.0
                else:
                    raw_score = (claims_grounded + (0.5 * claims_partially_supported)) / claims_applicable_count
                    faithfulness = round(max(0.0, min(1.0, raw_score)), 2)

                faithfulness_reason = "claim_level_citation_verification"
                cited = (citations_total > 0)
                if citations_applicable and not cited:
                    warnings.append("CITATIONS_NOT_DETECTED")
                if citations_invalid > 0:
                    warnings.append("INVALID_CITATION_INDEX_DETECTED")
                if claims_contradicted > 0:
                    warnings.append("EVIDENCE_CONTRADICTION_DETECTED")

                attribution_valid = (citations_invalid == 0 and claims_contradicted == 0 and claims_unsupported == 0)

                telemetry = {
                    "claims_total": len(extracted_claims),
                    "claims_applicable": claims_applicable_count,
                    "claims_grounded": claims_grounded,
                    "claims_partially_supported": claims_partially_supported,
                    "claims_unsupported": claims_unsupported,
                    "claims_contradicted": claims_contradicted,
                    "claims_invalid_citation": claims_invalid_citation,
                    "claims_no_citation": claims_no_citation,
                    "citations_total": citations_total,
                    "citations_valid": citations_valid,
                    "citations_invalid": citations_invalid,
                    "attribution_valid": attribution_valid,
                }

        if source_mode == "documents+web":
            has_documents_section = "Information from Indexed Documents" in answer
            has_web_section = "Information from External Web Sources" in answer
            if not (has_documents_section and has_web_section):
                warnings.append("MIXED_EVIDENCE_SECTIONS_MISSING")

        faith_log_str = f"{faithfulness:.2f}" if faithfulness is not None else "N/A (General Knowledge)"
        logger.info(
            f"Validation completed for query: '{query}' | Mode: {source_mode} | Strategy: {source_strategy} | "
            f"Faithfulness: {faith_log_str} | Warnings: {warnings}"
        )

        res_meta = {
            "faithfulness": faithfulness,
            "faithfulness_applicable": faithfulness_applicable,
            "faithfulness_reason": faithfulness_reason,
            "citations_applicable": citations_applicable,
            "citations_detected": cited,
            "source_mode": source_mode,
            "warnings": warnings,
        }
        res_meta.update(telemetry)

        return AgentResult(
            content=answer,
            confidence=0,
            agent_trace=[f"🛡️ Validation completed (Evidence Faithfulness: {faith_log_str}, Mode: {source_mode})"],
            metadata=res_meta,
            success=True
        )


