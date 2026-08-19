"""Response Composer assembling SynthesizedKnowledge into EducationalResponse objects."""

import time
from typing import List, Dict, Any, Optional

from core.models.verification import VerifiedKnowledgeCollection, VerifiedKnowledgeResult
from core.models.synthesis import SynthesizedKnowledge, EducationalResponse, LearningPath
from core.planner.execution_plan import ExecutionPlan
from core.synthesis.guided_learning import GuidedLearningEngine, guided_learning_engine
from core.logger import get_logger

logger = get_logger("core.synthesis.response_composer")


class ResponseComposer:
    """Assembles synthesized knowledge into structured EducationalResponse UI models."""

    def __init__(self, guided_engine: Optional[GuidedLearningEngine] = None):
        self.guided_engine = guided_engine or guided_learning_engine

    def compose_response(
        self,
        syn_knowledge: SynthesizedKnowledge,
        verified_collection: VerifiedKnowledgeCollection,
        plan: Optional[ExecutionPlan] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> EducationalResponse:
        """Compose structured EducationalResponse with layered sections, citations, and guided learning."""
        t0 = time.time()
        query = syn_knowledge.query
        results = verified_collection.verified_results

        exp_mode = plan.expected_output.value if plan and hasattr(plan.expected_output, "value") else "detailed_explanation"

        # Categorize Source Items into Layered Sections
        uploaded_notes = []
        trusted_web = []
        wikipedia = []
        research = []
        books = []
        videos = []
        code_examples = []
        citations = []
        providers_used = set()

        for idx, item in enumerate(results, 1):
            providers_used.add(item.provider)

            # Build Citation Object
            citation = {
                "id": idx,
                "title": item.title,
                "provider": item.provider,
                "source_type": item.source_type.value if hasattr(item.source_type, "value") else str(item.source_type),
                "url": item.url,
                "score": int(item.verification_score * 100),
            }
            citations.append(citation)

            item_dict = item.dict()
            st_val = str(item_dict.get("source_type", "")).lower()

            if "internal_document" in st_val:
                uploaded_notes.append(item_dict)
            elif "trusted_web" in st_val or "tavily" in st_val or "duckduckgo" in st_val or "fire_crawl" in st_val or "jina_reader" in st_val:
                trusted_web.append(item_dict)
            elif "wikipedia" in st_val:
                wikipedia.append(item_dict)
            elif "semantic_scholar" in st_val or "arxiv" in st_val:
                research.append(item_dict)
            elif "book" in st_val or "google_books" in st_val:
                books.append(item_dict)
            elif "video" in st_val or "youtube" in st_val:
                videos.append(item_dict)
            elif "github" in st_val:
                code_examples.append(item_dict)

        # Generate Guided Questions & Learning Path via Canonical Topic
        from core.synthesis.guided_learning import extract_canonical_topic
        canonical_topic = extract_canonical_topic(query, plan=plan)
        guided_qs = self.guided_engine.generate_guided_questions(query, topic=canonical_topic, plan=plan, history=history)
        l_path = self.guided_engine.generate_learning_path(query, topic=canonical_topic, plan=plan)

        # Create Short Polished Learning Summary
        summary = (
            f"Synthesized from {len(results)} verified sources across {len(providers_used)} providers. "
            f"Overall confidence score: {int(verified_collection.overall_confidence * 100)}%."
        )

        comp_latency = (time.time() - t0) * 1000
        logger.info(f"[ResponseComposer] Composed EducationalResponse in {int(comp_latency)}ms for query: '{query[:30]}...'")

        return EducationalResponse(
            query=query,
            educational_mode=exp_mode,
            ai_explanation=syn_knowledge.primary_explanation,
            uploaded_notes=uploaded_notes,
            trusted_web=trusted_web,
            wikipedia=wikipedia,
            research=research,
            books=books,
            videos=videos,
            code_examples=code_examples,
            key_takeaways=syn_knowledge.key_takeaways,
            important_terms=syn_knowledge.important_terms,
            learning_summary=summary,
            conflicts=verified_collection.conflicts,
            guided_questions=guided_qs,
            learning_path=l_path,
            citations=citations,
            providers_used=list(providers_used),
            confidence=verified_collection.overall_confidence if verified_collection.overall_confidence > 0 else (syn_knowledge.confidence or 0.85),
            agreement=verified_collection.overall_agreement,
            synthesis_metadata={
                "composer_latency_ms": comp_latency,
                "synthesis_latency_ms": syn_knowledge.metadata.get("latency_ms", 0.0),
                "total_sources": len(results),
                "provider": syn_knowledge.metadata.get("provider", "uploaded_documents" if uploaded_notes else "gemini"),
                "model": syn_knowledge.metadata.get("model", "gemini-2.5-flash"),
            }
        )



# Global singleton instance
response_composer = ResponseComposer()
