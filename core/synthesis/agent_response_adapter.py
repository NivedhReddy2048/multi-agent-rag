"""Deterministic Agent Response Adapter for EKIP Platform.

Converts authoritative AgentResult and runtime metadata into an EducationalResponse model
without executing any LLM calls or duplicate synthesis.
"""

from typing import Dict, Any, List, Optional
from core.models.synthesis import EducationalResponse, LearningPath
from core.planner.execution_plan import ExecutionPlan
from core.logger import get_logger

logger = get_logger("core.synthesis.agent_response_adapter")


class AgentResponseAdapter:
    """Deterministic adapter translating authoritative AgentResult into EducationalResponse."""

    def compose_from_agent_result(
        self,
        agent_result: Any,
        plan: Optional[ExecutionPlan] = None,
        history: Optional[List[Dict[str, Any]]] = None,
        planning_state: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Convert AgentResult to EducationalResponse dict deterministically."""
        content = getattr(agent_result, "content", "")
        confidence = getattr(agent_result, "confidence", 0.0)
        sources = getattr(agent_result, "sources", []) or []
        metadata = getattr(agent_result, "metadata", {}) or {}
        success = getattr(agent_result, "success", True)
        error = getattr(agent_result, "error", "")

        # 1. Determine Response Status
        response_status = metadata.get("response_status")
        if not response_status:
            if not success or error:
                response_status = "ERROR"
            elif metadata.get("failure_reason") == "INSUFFICIENT_EVIDENCE" or "couldn't find" in content.lower():
                response_status = "INSUFFICIENT_EVIDENCE"
            else:
                response_status = "SUCCESS"

        query = ""
        if plan and hasattr(plan, "query"):
            query = plan.query
        elif plan and hasattr(plan, "user_query"):
            query = plan.user_query
        elif planning_state and hasattr(planning_state, "question"):
            query = planning_state.question
        elif isinstance(metadata.get("execution_plan"), dict):
            query = metadata["execution_plan"].get("query", metadata["execution_plan"].get("user_query", ""))

        exp_mode = "detailed_explanation"
        if plan and hasattr(plan, "expected_output") and hasattr(plan.expected_output, "value"):
            exp_mode = plan.expected_output.value

        # 3. Categorize Sources & Build Citations
        uploaded_notes: List[Dict[str, Any]] = []
        trusted_web: List[Dict[str, Any]] = []
        wikipedia: List[Dict[str, Any]] = []
        research: List[Dict[str, Any]] = []
        books: List[Dict[str, Any]] = []
        videos: List[Dict[str, Any]] = []
        code_examples: List[Dict[str, Any]] = []
        citations: List[Dict[str, Any]] = []
        providers_used: set = set()

        if response_status == "SUCCESS":
            for idx, src in enumerate(sources, 1):
                prov = src.get("provider") or ("tavily" if ("web_" in str(src.get("chunk_id", "")) or "url" in src) else "uploaded_documents")
                providers_used.add(prov)

                title = src.get("title") or src.get("source_file") or f"Source {idx}"
                url = src.get("url", "")
                st_type = str(src.get("source_type", "")).lower()

                citations.append({
                    "id": idx,
                    "title": title,
                    "provider": prov,
                    "source_type": st_type or ("web" if "url" in src else "internal_document"),
                    "url": url,
                    "score": int(float(src.get("score", 0.0)) * 100),
                })

                src_dict = dict(src) if isinstance(src, dict) else {}
                if "internal_document" in st_type or "uploaded_documents" in prov:
                    uploaded_notes.append(src_dict)
                elif "trusted_web" in st_type or "tavily" in prov or "web" in st_type or "fire_crawl" in st_type or "jina_reader" in st_type:
                    trusted_web.append(src_dict)
                elif "wikipedia" in st_type:
                    wikipedia.append(src_dict)
                elif "semantic_scholar" in st_type or "arxiv" in st_type or "research" in st_type:
                    research.append(src_dict)
                elif "book" in st_type or "google_books" in st_type:
                    books.append(src_dict)
                elif "video" in st_type or "youtube" in st_type:
                    videos.append(src_dict)
                elif "github" in st_type or "code" in st_type:
                    code_examples.append(src_dict)
                else:
                    if "url" in src:
                        trusted_web.append(src_dict)
                    else:
                        uploaded_notes.append(src_dict)

        # Normalize confidence score cleanly (0.85 -> 0.85, 85 -> 0.85, 100 -> 1.0)
        def normalize_confidence(val: Any) -> float:
            if val is None:
                return 0.0
            try:
                f_val = float(val)
                if f_val > 1.0:
                    return round(min(1.0, f_val / 100.0), 4)
                return round(max(0.0, min(1.0, f_val)), 4)
            except (ValueError, TypeError):
                return 0.0

        conf_float = normalize_confidence(confidence)

        # Telemetry Hardening: Distinguish agreement from faithfulness
        raw_faithfulness = metadata.get("faithfulness")
        faithfulness_val = float(raw_faithfulness) if raw_faithfulness is not None else None

        raw_agreement = metadata.get("agreement") or metadata.get("overall_agreement")
        agreement_val = float(raw_agreement) if raw_agreement is not None else 0.0

        # 4. Extract or Reuse Guided Questions & Learning Path from Planning State / Guided Engine
        guided_qs: List[str] = []
        l_path_dict: Optional[Dict[str, Any]] = None

        if response_status == "SUCCESS":
            if planning_state:
                if hasattr(planning_state, "recommended_questions") and planning_state.recommended_questions:
                    guided_qs = planning_state.recommended_questions
                edu_state = getattr(planning_state, "educational_response", None) or getattr(planning_state, "provider_metadata", {}).get("educational_response")
                if isinstance(edu_state, dict):
                    guided_qs = guided_qs or edu_state.get("guided_questions", [])
                    l_path_dict = edu_state.get("learning_path")

            if not guided_qs or not l_path_dict:
                try:
                    from core.synthesis.guided_learning import guided_learning_engine, extract_canonical_topic
                    canonical_topic = extract_canonical_topic(query, plan=plan)
                    if not guided_qs:
                        guided_qs = guided_learning_engine.generate_guided_questions(query, topic=canonical_topic, plan=plan, history=history)
                    if not l_path_dict:
                        lp_obj = guided_learning_engine.generate_learning_path(query, topic=canonical_topic, plan=plan)
                        l_path_dict = lp_obj.dict() if hasattr(lp_obj, "dict") else lp_obj.model_dump()
                except Exception as gle_err:
                    logger.warning(f"[AgentResponseAdapter] Non-LLM guided learning fallback warning: {gle_err}")

        # 5. Deterministic Summary
        if response_status == "INSUFFICIENT_EVIDENCE":
            summary = "Insufficient document evidence found for query."
        elif response_status == "ERROR":
            summary = "Execution error occurred during pipeline processing."
        else:
            summary = (
                f"Authoritative synthesis from {len(sources)} sources across {len(providers_used) or 1} provider(s). "
                f"Confidence: {int(conf_float * 100)}%."
            )

        edu_model = EducationalResponse(
            query=query,
            educational_mode=exp_mode,
            ai_explanation=content,
            uploaded_notes=uploaded_notes,
            trusted_web=trusted_web,
            wikipedia=wikipedia,
            research=research,
            books=books,
            videos=videos,
            code_examples=code_examples,
            key_takeaways=metadata.get("key_takeaways", []) if response_status == "SUCCESS" else [],
            important_terms=metadata.get("important_terms", {}) if response_status == "SUCCESS" else {},
            learning_summary=summary,
            conflicts=metadata.get("conflicts", []) if response_status == "SUCCESS" else [],
            guided_questions=guided_qs,
            learning_path=LearningPath(**l_path_dict) if (isinstance(l_path_dict, dict) and response_status == "SUCCESS") else None,
            citations=citations,
            providers_used=list(providers_used),
            confidence=conf_float,
            agreement=agreement_val,
            synthesis_metadata={
                "response_status": response_status,
                "authoritative": True,
                "provider": metadata.get("provider", "gemini"),
                "model": metadata.get("model", "gemini-2.5-flash"),
                "total_sources": len(sources),
                "faithfulness": faithfulness_val,
                "faithfulness_applicable": metadata.get("faithfulness_applicable", True),
                "faithfulness_reason": metadata.get("faithfulness_reason", ""),
            }
        )

        resp_dict = edu_model.dict() if hasattr(edu_model, "dict") else edu_model.model_dump()
        resp_dict["response_status"] = response_status
        return resp_dict


# Global singleton instance
agent_response_adapter = AgentResponseAdapter()
