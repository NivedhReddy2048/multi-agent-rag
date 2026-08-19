"""Knowledge Synthesizer combining verified evidence into SynthesizedKnowledge objects."""

import time
import re
from typing import List, Dict, Any, Optional

from core.models.verification import VerifiedKnowledgeCollection, VerifiedKnowledgeResult
from core.models.synthesis import SynthesizedKnowledge
from core.planner.execution_plan import ExecutionPlan
from core.synthesis.prompt_builder import EducationalPromptBuilder
from core.llm_manager import LLMManager
from core.logger import get_logger

logger = get_logger("core.synthesis.knowledge_synthesizer")


class KnowledgeSynthesizer:
    """Evidence-aware synthesizer fusing verified knowledge items into structured synthesized knowledge."""

    def __init__(self, llm_manager: Optional[LLMManager] = None):
        self.prompt_builder = EducationalPromptBuilder()
        self.llm_manager = llm_manager or LLMManager()

    def synthesize(
        self,
        verified_collection: VerifiedKnowledgeCollection,
        plan: Optional[ExecutionPlan] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> SynthesizedKnowledge:
        """Synthesize verified evidence while preserving provenance and respecting conflicts."""
        t0 = time.time()
        query = verified_collection.query
        results = verified_collection.verified_results

        if not results:
            from core.planner.enums import SourceStrategy, EducationalIntent
            is_doc_req = plan and (
                getattr(plan, "source_strategy", None) == SourceStrategy.DOCUMENT_ONLY
                or getattr(plan, "intent", None) in (EducationalIntent.QUIZ_GENERATION, EducationalIntent.PRACTICE_QUIZ, "quiz_generation", "practice_quiz")
                or getattr(plan, "requires_internal_documents", False)
            )

            if is_doc_req:
                has_indexed_docs = False
                try:
                    from core.engine import BaseRAGEngine
                    eng = BaseRAGEngine.get_instance()
                    if eng and eng.list_docs():
                        has_indexed_docs = True
                except Exception:
                    pass

                if not has_indexed_docs:
                    explanation = "No uploaded or indexed documents were found in your workspace. Please upload documents in the Documents section before generating a practice quiz."
                else:
                    explanation = f"I couldn't find enough information about '{query}' in your indexed documents to create a document-grounded quiz. Please specify a document or topic from your uploaded material."

                return SynthesizedKnowledge(
                    query=query,
                    primary_explanation=explanation,
                    key_takeaways=["No relevant document evidence found in workspace."],
                    important_terms={},
                    confidence=0.0,
                    agreement=0.0,
                )

            logger.info("[KnowledgeSynthesizer] Empty verified collection provided; generating explanation via core LLM knowledge.")
            fallback_prompt = (
                f"You are EKIP, an AI Learning OS tutor. Provide a comprehensive, detailed, and clear educational explanation for: '{query}'.\n"
                "Explain the core concepts, mechanisms, and importance clearly in structured markdown paragraphs."
            )
            explanation = f"Educational explanation for '{query}'."
            try:
                llm_resp = self.llm_manager.generate(fallback_prompt, query=query, timeout=15.0)
                if llm_resp and llm_resp.content:
                    explanation = llm_resp.content.strip()
            except TypeError as te:
                logger.error(f"[KnowledgeSynthesizer] Programming/Interface Error in fallback LLM call: {te}", exc_info=True)
                raise
            except Exception as e:
                logger.warning(f"[KnowledgeSynthesizer] LLM generation failed for empty collection: {e}")

            return SynthesizedKnowledge(
                query=query,
                primary_explanation=explanation,
                key_takeaways=[f"Synthesized core educational principles for '{query}'."],
                important_terms={query.title(): f"Educational subject matter regarding {query}."},
                confidence=0.85,
                agreement=1.0,
            )


        # Separate Primary vs Supporting Evidence
        primary_results = [r for r in results if r.is_canonical and r.verification_score >= 0.65]
        supporting_results = [r for r in results if not r.is_canonical or r.verification_score < 0.65]

        # Extract Key Terms & Definitions from high-confidence items
        glossary = {}
        for r in results:
            if ":" in r.content and len(r.content.split(":")[0]) < 30:
                parts = r.content.split(":", 1)
                term = parts[0].strip().title()
                defn = parts[1].strip()[:150]
                if term and len(term) > 3 and term not in glossary:
                    glossary[term] = defn

        # Standard Key Takeaways
        takeaways = [
            f"Verified evidence collected from {len(set(r.provider for r in results))} independent knowledge providers.",
            f"Overall evidence confidence score is {int(verified_collection.overall_confidence * 100)}%.",
        ]
        if primary_results:
            takeaways.append(f"Primary canonical authority: '{primary_results[0].title}' ({primary_results[0].provider}).")

        # Provenance Mapping
        provenance = {
            "primary_sources_count": len(primary_results),
            "supporting_sources_count": len(supporting_results),
            "conflicts_count": len(verified_collection.conflicts),
            "providers_used": list(set(r.provider for r in results)),
        }

        # Try LLM Grounded Synthesis
        prompt = self.prompt_builder.build_synthesis_prompt(query, verified_collection, plan, history)
        primary_explanation = ""
        used_provider = "uploaded_documents" if any(r.provider == "uploaded_documents" for r in results) else "gemini"
        used_model = "gemini-2.5-flash"

        try:
            llm_resp = self.llm_manager.generate(prompt, query=query, timeout=15.0)
            if llm_resp and llm_resp.content:
                primary_explanation = llm_resp.content.strip()
                if hasattr(llm_resp, "provider") and llm_resp.provider:
                    used_provider = llm_resp.provider
                if hasattr(llm_resp, "model") and llm_resp.model:
                    used_model = llm_resp.model
        except TypeError as te:
            logger.error(f"[KnowledgeSynthesizer] Programming/Interface Error in LLM call: {te}", exc_info=True)
            raise
        except Exception as err:
            logger.warning(f"[KnowledgeSynthesizer] LLM provider failed, using rule-based synthesis fallback: {err}")

        if not primary_explanation:
            # Fallback Grounded Synthesis
            explanation_parts = []
            for idx, r in enumerate(primary_results[:3], 1):
                explanation_parts.append(f"**[{idx}] {r.title}** ({r.provider}):\n{r.content}")
            primary_explanation = "\n\n".join(explanation_parts) if explanation_parts else results[0].content

        syn_latency = (time.time() - t0) * 1000
        logger.info(f"[KnowledgeSynthesizer] Synthesized knowledge for query '{query[:30]}...' in {int(syn_latency)}ms")

        return SynthesizedKnowledge(
            query=query,
            primary_explanation=primary_explanation,
            supporting_explanations=[{"title": r.title, "content": r.content[:300], "provider": r.provider} for r in supporting_results],
            conflicting_views=verified_collection.conflicts,
            key_takeaways=takeaways,
            important_terms=glossary,
            provenance_map=provenance,
            confidence=verified_collection.overall_confidence if verified_collection.overall_confidence > 0 else 0.85,
            agreement=verified_collection.overall_agreement,
            metadata={
                "latency_ms": syn_latency,
                "provider": used_provider,
                "model": used_model,
            },
        )



# Global singleton instance
knowledge_synthesizer = KnowledgeSynthesizer()
