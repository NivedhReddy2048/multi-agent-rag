"""Evidence-Grounded Synthesis Agent for EKIP Platform.

Enforces zero-prior-knowledge generation based strictly on supplied context.
"""

import time
from typing import Dict, Any, Generator
from langchain_core.prompts import ChatPromptTemplate
from .base import BaseAgent, AgentResult
from core.logger import get_logger
from core.llm_manager import LLMManager

logger = get_logger("agents.synthesis")


class SynthesisAgent(BaseAgent):
    """Synthesis Agent producing strictly evidence-grounded LLM answers with citation tagging."""

    name = "synthesis"
    description = "Generates grounded answers strictly using supplied context"

    def __init__(self, config):
        self.cfg = config
        self.llm_manager = LLMManager(config)

    def _prepare_prompt_and_context(self, context: Dict[str, Any]):
        from core.synthesis.prompt_builder import EducationalPromptBuilder
        from core.models.verification import VerifiedKnowledgeCollection, VerifiedKnowledgeResult
        from core.planner.rules import RuleBasedPlannerEngine

        query = context["query"]
        docs = context.get("documents", [])
        history = context.get("history", [])
        intent = context.get("intent", "QA")
        source_mode = context.get("source_mode", "documents")

        plan = context.get("execution_plan")
        source_strat = context.get("source_strategy")
        if not source_strat and plan:
            source_strat = getattr(plan, "source_strategy", None)

        from core.planner.enums import SourceStrategy
        if isinstance(source_strat, SourceStrategy):
            is_strict = (source_strat == SourceStrategy.DOCUMENT_ONLY)
        elif source_strat:
            is_strict = (str(source_strat).lower() == "document_only")
        else:
            is_strict = False

        min_score = float(getattr(self.cfg, "MIN_RERANK_SCORE_STRICT", -1.0)) if is_strict else float(getattr(self.cfg, "MIN_RERANK_SCORE", 0.0))
        max_chunks = int(getattr(self.cfg, "MAX_EVIDENCE_CHUNKS", 6))
        max_chars = int(getattr(self.cfg, "MAX_EVIDENCE_CHARS", 3500))

        # 1. Filter surviving docs by MIN_RERANK_SCORE
        surviving_docs = [d for d in docs if "score" not in d or float(d.get("score", 0.0)) >= min_score]

        # 2. Dual-Context Split: Separate Factual Evidence from Learning Resources
        from core.planner.enums import SourceRole
        factual_docs = [
            d for d in surviving_docs
            if d.get("source_role") == SourceRole.FACTUAL_EVIDENCE.value
            or d.get("source_type") in ("internal_document", "trusted_web", "wikipedia", "arxiv", "semantic_scholar", "youtube", "github_repo", "google_books", "book")
        ]
        learning_resource_docs = [
            d for d in surviving_docs
            if d not in factual_docs
        ]

        # 3. Sort factual evidence by score descending and apply factual budget
        sorted_factual = sorted(factual_docs, key=lambda d: float(d.get("score", 0.0)), reverse=True)
        capped_factual = sorted_factual[:max_chunks]

        # 4. Apply character budget strictly to factual evidence
        budgeted_docs = []
        total_chars = 0
        for d in capped_factual:
            content = d.get("content") or d.get("snippet", "")
            if total_chars >= max_chars:
                break
            remaining_budget = max_chars - total_chars
            if len(content) > remaining_budget:
                truncated_d = dict(d)
                truncated_d["content"] = content[:remaining_budget]
                budgeted_docs.append(truncated_d)
                total_chars += remaining_budget
                break
            else:
                budgeted_docs.append(d)
                total_chars += len(content)

        verified_results = []
        for d in budgeted_docs:
            src = d.get("source_file", "Unknown")
            is_web = "web_" in str(d.get("chunk_id", "")) or "url" in d or "Web Search" in src
            title = d.get("title") or src
            content = d.get("content") or d.get("snippet", "")
            url = d.get("url", "")
            prov = d.get("provider") or ("tavily" if is_web else "uploaded_documents")
            st_type = d.get("source_type") or ("web" if is_web else "internal_document")

            doc_meta = dict(d.get("metadata", {})) if isinstance(d.get("metadata"), dict) else {}
            doc_meta.update({
                "source_file": src,
                "document_id": d.get("document_id"),
                "chunk_id": d.get("chunk_id"),
                "page_number": d.get("page_number", 1),
                "score": float(d.get("score", 0.0)),
                "relevance_confidence": float(d.get("relevance_confidence", 0.0)),
                "source_role": d.get("source_role", SourceRole.FACTUAL_EVIDENCE.value),
            })

            res = VerifiedKnowledgeResult(
                query=query,
                content=content,
                title=title,
                url=url,
                provider=prov,
                source_type=st_type,
                verification_score=float(d.get("score", 0.0)),
                is_canonical=True,
                metadata=doc_meta,
            )
            verified_results.append(res)

        conflicts = []
        if len(budgeted_docs) > 1:
            import re
            num_patterns = [
                (r'(\d+)\s*(attention heads|heads)', 'attention heads'),
                (r'(\d+)\s*(layers|blocks)', 'layer count'),
                (r'(\d+)\s*(embedding dimension|dimension)', 'embedding dimension'),
            ]
            doc_facts = {}
            for d in budgeted_docs:
                src_name = d.get("source_file") or d.get("title") or "Document"
                content_lower = (d.get("content") or "").lower()
                for pat, fact_type in num_patterns:
                    match = re.search(pat, content_lower)
                    if match:
                        val = match.group(1)
                        if fact_type not in doc_facts:
                            doc_facts[fact_type] = []
                        doc_facts[fact_type].append((src_name, val))
            
            for fact_type, entries in doc_facts.items():
                distinct_vals = set(val for _, val in entries)
                if len(distinct_vals) > 1:
                    src_a, val_a = entries[0]
                    src_b, val_b = entries[1]
                    conflicts.append({
                        "source_a": src_a,
                        "source_b": src_b,
                        "conflict_type": f"Discrepancy in {fact_type}: '{val_a}' in {src_a} vs '{val_b}' in {src_b}"
                    })

        verified_collection = VerifiedKnowledgeCollection(
            query=query,
            verified_results=verified_results,
            conflicts=conflicts,
            overall_confidence=0.85 if verified_results else 0.0,
            metadata={"learning_resources": learning_resource_docs},
        )


        plan = context.get("execution_plan")
        if not plan:
            plan = RuleBasedPlannerEngine.generate_plan(query, history)

        ctx_strat = context.get("source_strategy")
        if ctx_strat and plan and hasattr(plan, "source_strategy"):
            from core.planner.enums import SourceStrategy
            try:
                plan.source_strategy = SourceStrategy(str(ctx_strat).lower())
            except ValueError:
                pass

        prompt_builder = EducationalPromptBuilder()
        system_msg = prompt_builder.build_synthesis_prompt(
            query=query,
            verified_collection=verified_collection,
            plan=plan,
            history=history,
        )

        ctx_strat = context.get("source_strategy")
        if ctx_strat:
            prompt_template_name = str(ctx_strat).upper()
        elif plan and hasattr(plan, "source_strategy") and hasattr(plan.source_strategy, "value"):
            prompt_template_name = plan.source_strategy.value.upper()
        else:
            prompt_template_name = "GENERAL_KNOWLEDGE"

        prompt = ChatPromptTemplate.from_template("{system_prompt}")
        inputs = {"system_prompt": system_msg}

        telemetry = {
            "synthesis_evidence_chunk_count": len(budgeted_docs),
            "synthesis_evidence_char_count": total_chars,
            "rejected_by_rerank_count": len(docs) - len(surviving_docs),
            "min_rerank_score_used": min_score,
        }

        return prompt, inputs, intent, budgeted_docs, query, source_mode, prompt_template_name, system_msg, telemetry


    def run(self, context: Dict[str, Any]) -> AgentResult:
        import os
        t0 = time.time()
        prompt, inputs, intent, docs, query, source_mode, prompt_template_name, system_msg, telemetry = self._prepare_prompt_and_context(context)

        source_strat = str(context.get("source_strategy", "general_knowledge")).lower()
        decision = context.get("decision", "General Educational Lesson")

        # Phase 6 Assertions for GENERAL_KNOWLEDGE
        if source_strat == "general_knowledge" and source_mode == "general_knowledge":
            try:
                assert len(docs) == 0, f"Expected 0 docs for general_knowledge, got {len(docs)}"
                assert prompt_template_name == "GENERAL_KNOWLEDGE", f"Expected prompt_template 'GENERAL_KNOWLEDGE', got '{prompt_template_name}'"
            except AssertionError as ae:
                logger.error(f"[SYNTHESIS ASSERTION FAILURE] {ae}", exc_info=True)
                raise

        # Phase 2 Logging & Debug File Dump
        formatted_prompt = prompt.format(**inputs)
        logger.info(
            f"[Phase 2 Pre-LLM] Component: SynthesisAgent | Strategy: {source_strat} | "
            f"Decision: {decision} | Mode: {source_mode} | Template: {prompt_template_name} | "
            f"Doc Count: {len(docs)} | Sources Count: {len(docs)} | Prompt Len: {len(formatted_prompt)}"
        )

        os.makedirs("debug", exist_ok=True)
        with open("debug/final_prompt.txt", "w", encoding="utf-8") as f:
            f.write(f"=== EXECUTION METADATA ===\n")
            f.write(f"Strategy: {source_strat}\nDecision: {decision}\nMode: {source_mode}\nTemplate: {prompt_template_name}\nDoc Count: {len(docs)}\n\n")
            f.write(f"=== SYSTEM PROMPT ===\n{system_msg}\n\n")
            f.write(f"=== FINAL FORMATTED PROMPT ===\n{formatted_prompt}\n")

        timeout_val = getattr(self.cfg, "LLM_MAX_WAIT_SECONDS", getattr(self.cfg, "LLM_TIMEOUT_SECONDS", 15.0))

        llm_res = self.llm_manager.generate(
            prompt,
            inputs,
            temperature=0.1,
            max_tokens=4096,
            timeout=timeout_val,
            documents=docs,
            query=query,
            intent=intent,
        )

        # Phase 3 Raw LLM Response Dump
        logger.info(
            f"[Phase 3 Post-LLM] Provider: {llm_res.provider} | Model: {llm_res.model} | "
            f"Resp Len: {len(llm_res.content)} | Success: {llm_res.success} | Error: {llm_res.error}"
        )
        with open("debug/raw_llm_response.txt", "w", encoding="utf-8") as f:
            f.write(f"=== LLM RESPONSE METADATA ===\nProvider: {llm_res.provider}\nModel: {llm_res.model}\nSuccess: {llm_res.success}\nLatency: {llm_res.latency}ms\n\n")
            f.write(f"=== RAW CONTENT ===\n{llm_res.content}\n")

        latency = int((time.time() - t0) * 1000)
        self.last_metadata = {
            "latency_ms": latency,
            "intent": intent,
            "provider": llm_res.provider,
            "model": llm_res.model,
            "fallback_occurred": llm_res.fallback_occurred,
            "fallback_chain": llm_res.fallback_chain,
            "tokens": llm_res.tokens,
            "error": llm_res.error,
            "failure_reason": getattr(llm_res, "failure_reason", ""),
            "success": llm_res.success,
            "source_mode": source_mode,
            "prompt_builder_used": getattr(llm_res, "prompt_builder_used", True),
            "prompt_length_chars": getattr(llm_res, "prompt_length_chars", len(str(prompt))),
            "attempts_detail": getattr(llm_res, "attempts_detail", []),
            "synthesis_evidence_chunk_count": telemetry.get("synthesis_evidence_chunk_count", len(docs)),
            "synthesis_evidence_char_count": telemetry.get("synthesis_evidence_char_count", 0),
            "rejected_by_rerank_count": telemetry.get("rejected_by_rerank_count", 0),
            "min_rerank_score_used": telemetry.get("min_rerank_score_used", 0.0),
        }
        return AgentResult(
            content=llm_res.content,
            confidence=85 if (docs or source_mode in ("general_knowledge", "web", "documents+web") or llm_res.success) else 0,
            sources=docs,
            agent_trace=[f"Generated answer in {latency}ms (Provider: {llm_res.provider}, Mode: {source_mode})"],
            metadata=self.last_metadata,
            success=llm_res.success,
            error=llm_res.error,
        )


    def stream_synthesis(self, context: Dict[str, Any]) -> Generator[str, None, None]:
        """Streaming generator with multi-provider failover."""
        res = self.run(context)
        self.last_metadata = res.metadata
        yield res.content
