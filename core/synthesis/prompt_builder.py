"""Educational Prompt Builder for Grounded Multi-Source EKIP Synthesis."""

from typing import List, Dict, Any, Optional
from core.models.verification import VerifiedKnowledgeCollection, VerifiedKnowledgeResult
from core.planner.execution_plan import ExecutionPlan
from core.logger import get_logger

logger = get_logger("core.synthesis.prompt_builder")


class EducationalPromptBuilder:
    """Constructs structured educational prompts combining intent, difficulty, format, and verified evidence."""

    @staticmethod
    def _is_explicit_strict_document_query(query: str, plan: Optional[ExecutionPlan] = None) -> bool:
        """Determine whether the user explicitly requested answering strictly from uploaded document(s)."""
        q_lower = query.lower()
        strict_indicators = [
            "only from my document", "only from the document", "only from this document",
            "strictly from my document", "strictly from the document", "strictly from this document",
            "according to my uploaded document", "according to the uploaded document",
            "according to my document", "according to the document", "according to my pdf",
            "according to the pdf", "in my uploaded document", "in my uploaded file",
            "in my document", "in my pdf", "what does this document say",
            "what does the document say", "what does my document say",
            "summarize this pdf", "summarize this document", "summarize my uploaded document",
            "using only my uploaded", "using only my document", "from my document", "from my file"
        ]
        if any(ind in q_lower for ind in strict_indicators):
            return True
        if plan and getattr(plan, "target_documents", None):
            for doc in plan.target_documents:
                doc_stem = doc.lower().rsplit(".", 1)[0]
                if doc.lower() in q_lower or (len(doc_stem) > 4 and doc_stem in q_lower):
                    return True
        return False

    def build_synthesis_prompt(
        self,
        query: str,
        verified_collection: VerifiedKnowledgeCollection,
        plan: Optional[ExecutionPlan] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Build grounded, evidence-aware synthesis prompt for LLM generation."""
        intent = plan.intent.value if plan and hasattr(plan.intent, "value") else "Concept Explanation"
        difficulty = plan.difficulty.value if plan and hasattr(plan.difficulty, "value") else "Intermediate"
        exp_format = plan.expected_output.value if plan and hasattr(plan.expected_output, "value") else "Detailed Explanation"
        source_strat = (
            plan.source_strategy.value
            if plan and hasattr(plan, "source_strategy") and hasattr(plan.source_strategy, "value")
            else "general_knowledge"
        )
        is_doc_only = (source_strat == "document_only")

        factual_blocks = []
        for idx, item in enumerate(verified_collection.verified_results, 1):
            prov = item.provider
            st_type = item.source_type.value if hasattr(item.source_type, "value") else str(item.source_type)

            meta = item.metadata if isinstance(getattr(item, "metadata", None), dict) else {}
            page_num = meta.get("page_number", 1)
            chunk_id = meta.get("chunk_id", f"chunk_{idx}")
            extra_meta = ""
            if item.authors:
                extra_meta += f" | Authors: {', '.join(item.authors) if isinstance(item.authors, list) else item.authors}"
            if item.published_date:
                extra_meta += f" | Date: {item.published_date}"

            factual_blocks.append(
                f"[{idx}] Category: {st_type.upper()} | Title: {item.title} (via {prov}){extra_meta}\n"
                f"Page/Chunk: {page_num}/{chunk_id}\n"
                f"Content: {item.content[:800]}\n"
                f"URL/Link: {item.url or 'N/A'}"
            )

        learning_resources = (
            verified_collection.metadata.get("learning_resources", [])
            if isinstance(getattr(verified_collection, "metadata", None), dict)
            else []
        )

        resource_blocks = []
        for r in learning_resources:
            r_st = str(r.get("source_type", r.get("provider", "resource"))).upper()
            r_title = r.get("title", "Resource")
            r_url = r.get("url") or "N/A"
            r_extra = ""
            if r.get("channel_name"):
                r_extra += f" | Channel: {r.get('channel_name')}"
            if r.get("star_count") is not None:
                r_extra += f" | Stars: {r.get('star_count')}"
            if r.get("authors"):
                r_extra += f" | Authors: {', '.join(r.get('authors')) if isinstance(r.get('authors'), list) else r.get('authors')}"
            resource_blocks.append(f"- [{r_st}] {r_title}{r_extra} (URL: {r_url})")

        formatted_factual = "\n\n".join(factual_blocks) if factual_blocks else "No primary factual document evidence collected."
        formatted_resources = "\n".join(resource_blocks) if resource_blocks else "No external learning resources retrieved."

        formatted_evidence = (
            "==============================\n"
            "FACTUAL EVIDENCE (Primary Grounding Context)\n"
            "==============================\n"
            f"{formatted_factual}\n\n"
            "==============================\n"
            "SUPPLEMENTARY LEARNING RESOURCES (Recommendations & Context)\n"
            "==============================\n"
            f"{formatted_resources}"
        )

        conflicts_block = ""
        if verified_collection.conflicts:
            conflicts_txt = "\n".join([f"- {c.get('source_a')} vs {c.get('source_b')}: {c.get('conflict_type')}" for c in verified_collection.conflicts])
            conflicts_block = f"\n⚠️ DETECTED CONFLICTS IN EVIDENCE:\n{conflicts_txt}\nRule: Do NOT merge these conflicting claims silently. You MUST explicitly state this conflict in your response by source name.\n"

        is_quiz = (
            intent in ["quiz_generation", "practice_quiz"]
            or exp_format == "quiz"
            or any(w in query.lower() for w in ["quiz", "test me", "practice question", "exam question", "mcq", "multiple choice"])
        )

        if is_quiz:
            import re
            num_match = re.search(r'\b(\d+)\b', query)
            num_questions = int(num_match.group(1)) if num_match else 5
            target_str = f" for {', '.join(plan.target_documents)}" if (plan and getattr(plan, 'target_documents', None)) else ""

            prompt = f"""You are EKIP, an Educational Knowledge & Intelligence Platform tutor.
Student Quiz Request: "{query}"

Strict Pedagogical Directives for Practice Quiz Generation:
- Goal: Generate EXACTLY {num_questions} multiple-choice quiz questions grounded strictly in the VERIFIED KNOWLEDGE EVIDENCE below{target_str}.
- Target Learner Difficulty: {difficulty.upper()}
- Source Strategy: {source_strat}

VERIFIED KNOWLEDGE EVIDENCE:
{formatted_evidence}
{conflicts_block}

CRITICAL GROUNDING & SAFETY CONSTRAINTS:
1. Grounding: EVERY question, option choice (A, B, C, D), and correct answer MUST be directly answerable from the VERIFIED KNOWLEDGE EVIDENCE provided above.
2. DO NOT invent, extrapolate, or hallucinate facts, dates, scientific measurements, terminology, spacecraft, or entities not present in the evidence.
3. DO NOT write an educational guide, essay, overview, or meta-lesson explaining NLP, text analysis, sentiment analysis, document indexing, or how quiz generation works.
4. If the provided evidence above is empty or does NOT contain relevant information for "{query}" (or if no relevant document evidence is available for the requested topic), respond ONLY with:
   "I couldn't find enough information about '{query}' in your indexed documents to create a document-grounded quiz. Please specify a document or topic from your uploaded material."
   Do NOT fall back to general knowledge (e.g. interpreting RAG as Red/Amber/Green or inventing general facts).

REQUIRED OUTPUT STRUCTURE:
Output EXACTLY {num_questions} multiple-choice questions formatted in clean markdown as follows:

### 📝 Practice Quiz

#### Question 1
[Question text grounded in evidence]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
**Answer**: [Correct Option Letter] - [Brief justification referencing evidence]
**Source**: [Document Title / Source Name]

#### Question 2
...
"""
            return prompt

        is_multi_doc_summary = any(k in query.lower() for k in ["summarize my notes", "summarize my uploaded", "uploaded study notes", "summary of my documents", "summarize my files", "summarize all my notes"])
        is_explicit_strict = self._is_explicit_strict_document_query(query, plan)

        if is_multi_doc_summary:
            grounding_directive = (
                "1. This is a multi-document summary request across uploaded study notes.\n"
                "Organize the response into distinct sections for EACH uploaded document present in the evidence above.\n"
                "Use a separate heading for each document (e.g. '#### 📄 Document_Name').\n"
                "Summarize the key contents of each document independently and fairly. Never omit smaller documents."
            )
        elif is_doc_only:
            target_str = f" for {', '.join(plan.target_documents)}" if (plan and getattr(plan, 'target_documents', None)) else ""
            grounding_directive = (
                f"1. STRICT DOCUMENT GROUNDING & CITATION COMPLIANCE PROTOCOL{target_str}:\n"
                "- Base your explanation strictly on the VERIFIED KNOWLEDGE EVIDENCE provided above.\n"
                "- SENTENCE-LEVEL CITATION MANDATE: Every single factual sentence or claim derived from the uploaded evidence MUST contain at least one valid inline citation marker (e.g., [1], [2]).\n"
                "- CITATION ANCHORING: Citations MUST immediately follow the specific factual statement they support. Do NOT place a single citation at the end of a long paragraph containing multiple distinct facts.\n"
                "- VALID CITATIONS ONLY: Do NOT invent citation numbers. ONLY use citation indexes that explicitly exist in the provided evidence list above.\n"
                "- FEW-SHOT CITATION FORMATTING EXAMPLE:\n"
                "  \"The EKIP-MiniTransformer architecture uses 8 attention heads [1]. It features an embedding dimension of 256 [2].\"\n"
                "- MISSING EVIDENCE RULE: If requested information is not contained in the supplied evidence (or if evidence covers only part of the question):\n"
                "  a. Answer all information directly supported by the evidence with inline citations.\n"
                "  b. Explicitly state under a section heading '### ⚠️ Unsupported Information / Missing from Document' what information the document does not contain, or state transparently: 'I couldn't find relevant information about your query in the provided documents.'\n"
                "  c. DO NOT use outside model knowledge or general facts to complete missing details or fill unsupported sections.\n"
                "- CONFLICT HARDENING: If retrieved evidence documents contain conflicting facts or numbers (such as Source A stating 8 attention heads while Source B states 12), you MUST explicitly report this conflict in your answer by source name (e.g., 'Note: The provided sources conflict: doc_conf_a.txt states 8 attention heads, while doc_conf_b.txt states 12'). Do NOT silently synthesize a generic compromise."
            )


        elif intent in ("Research Discovery", "RESEARCH_DISCOVERY", "Research") or source_strat == "research":
            grounding_directive = (
                "1. RESEARCH DISCOVERY PROTOCOL:\n"
                "- Present the retrieved academic research papers and preprints directly to the user.\n"
                "- For EACH retrieved paper in the evidence, clearly format: Title, Authors, Publication Date, Source (arXiv/Semantic Scholar), URL/PDF link, and full Abstract.\n"
                "- Provide an overarching synthesis summarizing the state of research across the papers."
            )
        elif intent in ("Video Recommendation", "VIDEO_RECOMMENDATION") or source_strat == "video":
            grounding_directive = (
                "1. VIDEO RECOMMENDATION PROTOCOL:\n"
                "- Present the retrieved learning video recommendations clearly to the user.\n"
                "- For EACH retrieved video in the evidence, format: Video Title, Channel/Publisher, Video URL, and a brief description of why it is recommended.\n"
                "- Do NOT invent video titles or URLs."
            )
        elif intent in ("Code Resource Recommendation", "CODE_RESOURCE_RECOMMENDATION") or "github" in str(source_strat).lower():
            grounding_directive = (
                "1. CODE RESOURCE RECOMMENDATION PROTOCOL:\n"
                "- Present the retrieved open-source code repositories clearly to the user.\n"
                "- For EACH repository in the evidence, format: Repository Name (e.g. owner/repo), Language & Stars, GitHub URL, and relevance description.\n"
                "- Do NOT invent repository URLs."
            )
        else:
            grounding_directive = (
                "1. NORMAL EDUCATIONAL MODE & EVIDENCE RELEVANCE PROTOCOL:\n"
                "- Base technical explanations and factual claims primarily on the FACTUAL EVIDENCE block provided above.\n"
                "- Do NOT treat YouTube titles, repository descriptions, or book metadata in SUPPLEMENTARY LEARNING RESOURCES as factual proof of technical claims.\n"
                "- LEARNING RESOURCES are supplementary recommendations: introduce or highlight them naturally when relevant to the student's request, but do not allow them to crowd out the core explanation.\n"
                "- Evaluate whether each retrieved source is genuinely relevant to answering '{query}'.\n"
                "- If retrieved evidence is unrelated or weakly related: DO NOT allow it to block or distort your answer. Use general model knowledge to provide a complete, high-quality educational explanation.\n"
                "- Do NOT invent citations. ONLY attach inline citation numbers like [1], [2] for claims explicitly supported by FACTUAL EVIDENCE."
            )


        history_str = ""
        if history:
            history_lines = [f"{'User' if m.get('role')=='user' else 'Assistant'}: {str(m.get('content', ''))[:250]}" for m in history[-4:]]
            history_str = "Conversation History:\n" + "\n".join(history_lines) + "\n\n"

        citation_reminder = ""
        if is_doc_only:
            citation_reminder = (
                "\n\nCRITICAL FINAL MANDATE FOR DOCUMENT MODE:\n"
                "You MUST attach inline bracketed citation markers e.g. [1], [2] immediately after EVERY factual claim or sentence derived from the verified evidence above.\n"
                "Do NOT write paragraphs without inline citations. Example: 'The EKIP architecture uses 8 attention heads [1].'"
            )

        prompt = f"""You are EKIP, an expert educational AI tutor designed to help users deeply understand topics.

{history_str}Student Question: "{query}"

Pedagogical Directives:
- Target Learner Difficulty: {difficulty.upper()}
- Educational Intent: {intent}
- Requested Output Format: {exp_format}
- Source Strategy: {source_strat}

VERIFIED KNOWLEDGE EVIDENCE:
{formatted_evidence}
{conflicts_block}

PEDAGOGICAL & EXPLANATION FRAMEWORK:
{grounding_directive}

2. STRUCTURE & EXPLANATION PROGRESSION:
   For explanatory or conceptual questions, guide the learner naturally through this flow:
   a. **Problem & Motivation ("Why before How")**: What problem does this concept solve? Why was it introduced? What limitations existed before it?
   b. **Core Intuition**: Explain the foundational mental model before diving into technical details.
   c. **Major Components & Architecture**: Explain what each key component is, why it exists, how it works, and how it connects to the system.
   d. **Step-by-Step Workflow**: Walk through the mechanism or process clearly.
   e. **Practical Examples & Analogies**: Provide clear scenarios or real-world applications (e.g. BERT, GPT, T5, or practical domain examples) to solidify understanding.
   f. **Trade-offs & Limitations**: Mention important assumptions, bottlenecks, or failure cases when relevant.
   g. **Integrated Conclusion**: End with a connected summary that ties the major concepts together naturally (avoid shallow, repetitive bullet point lists).

3. TECHNICAL DEPTH & CLARITY:
   - Introduce technical terms with context rather than dumping unexplained jargon.
   - Match technical depth to {difficulty.upper()} level and {intent} intent.
   - Do NOT abbreviate explanations with generic filler or shallow placeholder bullets.{citation_reminder}
"""
        return prompt
