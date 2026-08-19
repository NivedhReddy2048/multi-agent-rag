"""EKIP Deterministic Rule-Based Planning Engine.

Executes zero-network, rule-based planning analysis for intent, difficulty, sources, strategy, and execution plan.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from core.models.domain import SourceType
from core.planner.enums import (
    EducationalIntent,
    DifficultyLevel,
    SourceStrategy,
    RetrievalStrategy,
    ExpectedOutputFormat,
    LatencyEstimate,
    CostEstimate,
    DocumentUsageMode,
)
from core.planner.execution_plan import ExecutionPlan


class RuleBasedPlannerEngine:
    """Deterministic rule-based decision engine for knowledge planning."""

    @staticmethod
    def resolve_target_documents(query: str, available_docs: Optional[List[str]] = None) -> List[str]:
        """Parse query and match against available document registry/filenames to resolve target documents."""
        if available_docs is None:
            try:
                from core.engine import BaseRAGEngine
                engine = BaseRAGEngine.get_instance()
                if engine:
                    available_docs = list(engine.list_docs().keys())
            except Exception:
                pass
        available_docs = available_docs or []

        q_lower = query.lower()
        matched_docs = set()

        generic_stems = {"notes", "file", "doc", "report", "pdf", "text", "summary", "paper", "data", "info", "overview", "guide", "details", "rag", "ai", "basics", "intro"}

        for doc_name in available_docs:
            doc_lower = doc_name.lower()
            stem = doc_lower.rsplit('.', 1)[0]
            clean_stem = re.sub(r'[^a-z0-9]', ' ', stem)

            # 1. Exact filename match or literal document name in query
            if doc_lower in q_lower or doc_name in query:
                matched_docs.add(doc_name)
                continue

            # 2. Whole-word stem match (only if stem is >= 5 chars AND NOT in generic stems)
            if len(stem) >= 5 and stem not in generic_stems and re.search(r'\b' + re.escape(stem) + r'\b', q_lower):
                matched_docs.add(doc_name)
                continue

            # 3. Specific explicit alias rules (whole-word boundary checks)
            if "coverletter" in doc_lower or "cover" in doc_lower:
                if any(re.search(r'\b' + re.escape(k) + r'\b', q_lower) for k in ["coverletter", "cover letter", "stripe cover", "my cover letter", "coverletter_stripe"]):
                    matched_docs.add(doc_name)
                    continue

            if "ai_arch" in doc_lower:
                if any(re.search(r'\b' + re.escape(k) + r'\b', q_lower) for k in ["ai_arch", "ai arch", "ai architecture", "architecture doc", "ai_arch.txt"]):
                    matched_docs.add(doc_name)
                    continue

            if "deep_solar" in doc_lower or "solar_system" in doc_lower:
                if any(re.search(r'\b' + re.escape(k) + r'\b', q_lower) for k in ["solar system", "deep solar", "planet report", "solar pdf", "solar system pdf"]):
                    matched_docs.add(doc_name)
                    continue

            if "venus" in doc_lower:
                if any(re.search(r'\b' + re.escape(k) + r'\b', q_lower) for k in ["venus express", "venus.pdf", "venus document"]):
                    matched_docs.add(doc_name)
                    continue

            if "mars" in doc_lower:
                if any(re.search(r'\b' + re.escape(k) + r'\b', q_lower) for k in ["marsreview", "mars review", "mars document", "mars volcanism"]):
                    matched_docs.add(doc_name)
                    continue

            # 4. Non-generic stem word match requiring all non-generic stem words (>= 4 chars) on word boundaries (plural-insensitive)
            non_generic_stem_words = [w for w in clean_stem.split() if len(w) >= 4 and w not in generic_stems]
            if non_generic_stem_words:
                matches = sum(1 for w in non_generic_stem_words if re.search(r'\b' + re.escape(w.rstrip('s')) + r'(?:s|es)?\b', q_lower))
                if matches >= len(non_generic_stem_words):
                    matched_docs.add(doc_name)

        return sorted(list(matched_docs))

    @staticmethod
    def determine_document_usage_mode(
        query: str,
        intent: EducationalIntent,
        target_docs: Optional[List[str]] = None,
        available_docs: Optional[List[str]] = None,
    ) -> Tuple[DocumentUsageMode, str]:
        """Determine deterministic DocumentUsageMode (REQUIRED, PREFERRED, OPTIONAL, EXCLUDED)."""
        q_lower = query.lower()

        explicit_doc_phrases = [
            "uploaded", "my notes", "lecture notes", "my document", "my file", "my pdf",
            "this pdf", "this file", "this document", "my report", "workspace",
            "uploaded pdf", "uploaded file", "uploaded document", "uploaded notes",
            "uploaded material", "search my documents", "answer using my notes",
            "find in my documents", "from my document", "in my notes", "with my file",
            "in my uploaded", "according to my", "according to the document",
            "using only", "strictly from", "only from", ".pdf", ".txt", ".docx"
        ]

        has_explicit_phrase = any(
            w in q_lower if w.startswith(".") else bool(re.search(r'\b' + re.escape(w) + r'\b', q_lower))
            for w in explicit_doc_phrases
        )

        has_explicit_filename = False
        if target_docs:
            for doc in target_docs:
                doc_lower = doc.lower()
                if doc_lower in q_lower:
                    has_explicit_filename = True
                    break

        if has_explicit_phrase or has_explicit_filename or intent in (EducationalIntent.DOCUMENT_QUERY, EducationalIntent.STUDY_NOTES):
            if available_docs is not None and len(available_docs) == 0:
                return DocumentUsageMode.OPTIONAL, "Document targeted but no uploaded documents exist in workspace; falling back gracefully to external search."
            return DocumentUsageMode.REQUIRED, "Query explicitly requests or targets uploaded documents."

        if target_docs and len(target_docs) > 0:
            return DocumentUsageMode.PREFERRED, "Query matches topic of uploaded document; preferring document context alongside external sources."

        return DocumentUsageMode.EXCLUDED, "No document reference or topic overlap; excluding internal document retrieval."

    @staticmethod
    def normalize_query(query: str) -> str:
        """Normalize informal phrasing and common educational typos without corrupting technical terms."""
        if not query:
            return ""
        # Collapse 3+ repeated letters (e.g., plzzzz -> plz, fasttt -> fast)
        q = re.sub(r'([a-zA-Z])\1{2,}', r'\1', query)
        q_lower = q.lower()
        replacements = [
            (r'\bplz\b|\bplzz+\b|\bpls\b', 'please'),
            (r'\bcan u\b', 'can you'),
            (r'\bneed 2\b', 'need to'),
            (r'\bgimme sum\b', 'give me some'),
            (r'\bvids\b', 'videos'),
            (r'\bvid\b', 'video'),
            (r'\bcode up\b', 'implement'),
            (r'\bdiff between\b', 'difference between'),
            (r'\bpythn\b', 'python'),
        ]
        norm = q_lower
        for pattern, repl in replacements:
            norm = re.sub(pattern, repl, norm)
        return norm

    @staticmethod
    def classify_intent(query: str, history: List[Dict[str, Any]]) -> Tuple[EducationalIntent, str]:
        norm_query = RuleBasedPlannerEngine.normalize_query(query)
        q_lower = norm_query.lower()

        # 1. Follow-up intent check
        followup_phrases = [
            "that second point", "second point", "third option", "that option",
            "that explanation", "that alternative", "code snippet for that", "why is that better",
            "example of the third", "what did you mean by", "in that explanation",
            "more on that", "papers about that"
        ]
        if any(p in q_lower for p in followup_phrases) or (
            history and len(history) >= 2 and any(w in q_lower for w in ["now ", "that ", "recommend ", "papers about that", "more on that", "what about"])
        ):
            if any(w in q_lower for w in ["paper", "research", "arxiv"]):
                return EducationalIntent.RESEARCH_DISCOVERY, "Follow-up query requesting research papers on prior topic."
            return EducationalIntent.FOLLOW_UP, "Follow-up query referencing prior context or session state."

        # 2. DOCUMENT_QUERY: Explicit document references take top precedence
        doc_query_phrases = [
            "uploaded pdf", "workspace", "my document", "uploaded document",
            "my file", "uploaded file", "this document", "this file", "in my document",
            "in my file", "according to my document", "according to the uploaded file",
            "what does my file say", "what does my document say", "summarize my document",
            "summarize my file"
        ]
        is_explicit_doc = any(w in q_lower for w in doc_query_phrases) or (
            any(prefix in q_lower for prefix in ["my ", "uploaded ", "this ", "in my ", "according to my "])
            and any(target in q_lower for target in ["document", "file", "pdf"])
        )
        if is_explicit_doc:
            return EducationalIntent.DOCUMENT_QUERY, "Query explicitly targets uploaded documents."

        # 3. RESEARCH_DISCOVERY (Word-boundary checks to avoid matching 'researcher' or 'researching')
        research_keywords = [
            "paper", "papers", "arxiv", "journal", "publication", "survey",
            "literature", "academic paper", "academic papers", "research paper",
            "research papers", "semantic scholar", "preprint", "preprints", "recent papers"
        ]
        has_research_phrase = any(w in q_lower for w in research_keywords) or bool(
            re.search(r'\bresearch\b', q_lower) and not re.search(r'\bresearcher\b|\bresearching\b', q_lower)
        )
        if has_research_phrase:
            return EducationalIntent.RESEARCH_DISCOVERY, "Query contains research paper discovery keywords."

        # 4. INTERVIEW_PREPARATION (Must precede PROGRAMMING_HELP and CAREER_GUIDANCE)
        if any(w in q_lower for w in ["interview", "interview question", "interview questions", "interview prep", "mock question"]):
            return EducationalIntent.INTERVIEW_PREPARATION, "Query requests interview prep."

        # 5. CAREER_GUIDANCE (Must precede PROGRAMMING_HELP)
        career_phrases = [
            "how do i become", "how to become", "become a", "career in", "career path",
            "job role", "career guidance", "what career", "professional path", "becoming a",
            "career", "profession", "transition", "transition to", "transition from",
            "how to transition", "how do i transition", "skills needed", "skills are needed",
            "skills required", "skills for"
        ]
        if any(w in q_lower for w in career_phrases):
            return EducationalIntent.CAREER_GUIDANCE, "Query requests career guidance."

        # 6. QUIZ_GENERATION, PRACTICE_QUIZ, STUDY_NOTES, FLASHCARDS
        if "practice quiz" in q_lower:
            return EducationalIntent.PRACTICE_QUIZ, "Query requests a practice quiz."

        quiz_keywords = [
            "quiz", "test me", "practice question", "exam question",
            "mcq", "mcqs", "multiple choice", "create questions", "generate questions",
            "question bank", "test questions", "quiz me", "create a quiz", "generate a quiz"
        ]
        if any(w in q_lower for w in quiz_keywords) and not ("roadmap" in q_lower or "learning path" in q_lower):
            return EducationalIntent.QUIZ_GENERATION, "Query requests quiz or practice question generation."

        if any(w in q_lower for w in ["study notes", "summarize my notes", "lecture notes"]):
            return EducationalIntent.STUDY_NOTES, "Query requests study note synthesis."

        if any(w in q_lower for w in ["flashcard", "cards", "memo cards"]):
            return EducationalIntent.FLASHCARDS, "Query requests flashcards."

        # 7. VIDEO_RECOMMENDATION
        if any(w in q_lower for w in ["video", "videos", "vids", "youtube", "watch", "tutorial video", "video lecture", "youtube videos", "video tutorials"]):
            return EducationalIntent.VIDEO_RECOMMENDATION, "Query requests video recommendations."

        # 8. CODE_RESOURCE_RECOMMENDATION (Must precede PROGRAMMING_HELP)
        code_resource_phrases = [
            "open source", "open-source", "github", "repo", "repository", "repositories",
            "codebase", "open source project", "implementation repository", "example project",
            "reference implementation", "python libraries", "libraries for", "packages for"
        ]
        if any(w in q_lower for w in code_resource_phrases):
            return EducationalIntent.CODE_RESOURCE_RECOMMENDATION, "Query requests GitHub code resources."

        # 9. COMPARISON
        if any(w in q_lower for w in ["compare", " vs ", "versus", "difference between", "diff between", "comparison"]):
            return EducationalIntent.COMPARISON, "Query requests a comparison between topics."

        # 10. ROADMAP
        if any(w in q_lower for w in ["roadmap", "learning path", "how to learn", "curriculum"]):
            return EducationalIntent.ROADMAP, "Query requests a learning roadmap."

        # 11. BOOK_RECOMMENDATION
        if any(w in q_lower for w in ["book", "textbook", "reading list", "novel", "recommended books"]):
            return EducationalIntent.BOOK_RECOMMENDATION, "Query requests book literature."

        # 12. PROGRAMMING_HELP (Action & Task specific)
        prog_action_phrases = [
            "write code", "write a script", "write a program", "write python", "how to write",
            "how to fix", "fix error", "fix bug", "fix indexerror", "solve error", "debug",
            "traceback", "exception", "script to", "program to", "implement", "implementation of",
            "build an api", "create an api", "api endpoint", "code snippet", "code example",
            "code for", "python script", "function to", "def ", "bug", "dockerfile", "write a dockerfile",
            "connect postgresql", "connect database", "how to connect", "using pg library",
            "how to handle", "how to configure", "how to integrate", "how to setup", "how to set up",
            "handle transactions", "configure authentication", "configure auth", "integrate stripe", "setup auth", "set up auth"
        ]
        has_prog_action = any(w in q_lower for w in prog_action_phrases) or bool(re.search(r'\brefactor\b', q_lower))

        framework_terms = ["django", "fastapi", "flask", "react", "spring boot"]
        has_framework = any(w in q_lower for w in framework_terms)
        has_impl_verb = any(v in q_lower for v in [
            "implement", "build", "create", "how to", "code", "authentication",
            "endpoint", "debug", "fix", "handle", "integrate", "configure", "setup", "set up"
        ])
        framework_action = has_framework and has_impl_verb

        conceptual_triggers = [
            "what is", "what are", "explain", "define", "definition", "concept of",
            "overview of", "tell me about", "how does", "how do"
        ]
        has_conceptual_phrase = any(w in q_lower for w in conceptual_triggers)

        # Explicit programming action or implementation task
        if has_prog_action or framework_action:
            # If query has conceptual phrasing BUT also explicit implementation verbs (e.g. "explain how to implement"), action wins
            if not has_conceptual_phrase or any(v in q_lower for v in ["implement", "write", "fix", "debug", "script", "code", "handle", "integrate", "configure", "setup"]):
                return EducationalIntent.PROGRAMMING_HELP, "Query requests programming or code assistance."

        # 13. TOPIC_SUMMARY
        if any(w in q_lower for w in ["summarize", "summary", "overview"]):
            return EducationalIntent.TOPIC_SUMMARY, "Query requests a topic summary."

        # 14. WEB_INFORMATION
        if any(w in q_lower for w in ["latest", "recent news", "today", "current", "web search", "online"]):
            return EducationalIntent.WEB_INFORMATION, "Query requests live web search information."

        return EducationalIntent.CONCEPT_EXPLANATION, "Default educational intent: concept explanation."

    @staticmethod
    def estimate_difficulty(query: str, history: List[Dict[str, Any]], intent: EducationalIntent) -> Tuple[DifficultyLevel, str]:
        q_lower = query.lower()

        research_terms = ["diffusion", "quantile", "eigenvalue", "asymptotic", "np-hard", "proof", "benchmark", "loss function", "state-of-the-art", "sota"]
        advanced_terms = ["architecture", "transformer", "cross-encoder", "backpropagation", "hyperparameter", "fine-tuning", "rag vs crag", "latent space"]
        beginner_terms = ["what is", "define", "introduction", "basics", "simple", "beginner", "easy", "overview"]

        if intent in (EducationalIntent.RESEARCH, EducationalIntent.RESEARCH_DISCOVERY) or any(t in q_lower for t in research_terms):
            return DifficultyLevel.RESEARCH, "Requires academic research & advanced mathematical / domain depth."
        if any(t in q_lower for t in advanced_terms) or "compare" in q_lower:
            return DifficultyLevel.ADVANCED, "Requires advanced conceptual understanding and architectural analysis."
        if any(t in q_lower for t in beginner_terms):
            return DifficultyLevel.BEGINNER, "Foundational query suitable for beginner introduction."

        if len(history) >= 4:
            return DifficultyLevel.INTERMEDIATE, "Multi-turn conversation indicates progressing intermediate student context."

        return DifficultyLevel.INTERMEDIATE, "Default intermediate educational difficulty."

    @staticmethod
    def determine_source_strategy(
        query: str,
        intent: EducationalIntent,
        history: List[Dict[str, Any]],
        target_docs: Optional[List[str]] = None
    ) -> Tuple[SourceStrategy, str]:
        q_lower = query.lower()

        if intent in (EducationalIntent.QUIZ_GENERATION, EducationalIntent.PRACTICE_QUIZ):
            if any(w in q_lower for w in ["web search", "online", "recent news", "search online"]):
                return SourceStrategy.WEB_AUGMENTED, "Quiz request specified external web search."
            doc_indicators = ["my doc", "my document", "document", "uploaded", "pdf", "file", "my notes", "this text"]
            if target_docs or any(w in q_lower for w in doc_indicators):
                return SourceStrategy.DOCUMENT_ONLY, "Practice quiz intent detected for document; retrieving exclusively from uploaded documents."
            return SourceStrategy.GENERAL_KNOWLEDGE, "General practice quiz request; utilizing general educational knowledge."

        doc_mode, _ = RuleBasedPlannerEngine.determine_document_usage_mode(query, intent, target_docs)

        if doc_mode == DocumentUsageMode.REQUIRED:
            compare_words = ["compare", " vs ", "versus", "difference", "standard", "general", "external"]
            is_strict_lock = any(k in q_lower for k in ["using only", "strictly from", "only from", "only in my"])
            if any(w in q_lower for w in compare_words) and not is_strict_lock:
                return SourceStrategy.DOCUMENT_AUGMENTED, "Explicit document request with comparison/external search."
            return SourceStrategy.DOCUMENT_ONLY, "Explicit document request strictly targeting uploaded documents."

        if doc_mode == DocumentUsageMode.PREFERRED:
            return SourceStrategy.DOCUMENT_AUGMENTED, "Topic overlap detected with uploaded document; preferring document context alongside external sources."

        if intent in (EducationalIntent.RESEARCH, EducationalIntent.RESEARCH_DISCOVERY) or any(w in q_lower for w in ["paper", "arxiv", "scholar", "literature", "journal", "publication", "academic papers", "research papers"]):
            return SourceStrategy.RESEARCH, "Research intent detected; targeting academic paper databases."

        if intent == EducationalIntent.WEB_INFORMATION or any(w in q_lower for w in ["latest", "recent news", "today", "current", "web search", "search online"]):
            return SourceStrategy.WEB_AUGMENTED, "Live web search intent detected."

        if intent in (EducationalIntent.VIDEO_RECOMMENDATION, EducationalIntent.BOOK_RECOMMENDATION, EducationalIntent.PROGRAMMING_HELP, EducationalIntent.CODE_RESOURCE_RECOMMENDATION) or any(w in q_lower for w in ["video", "youtube", "book", "github", "repo"]):
            return SourceStrategy.HYBRID, "Multi-media educational resources requested."

        return SourceStrategy.GENERAL_KNOWLEDGE, "General educational question; utilizing LLM core knowledge and Wikipedia without document retrieval."

    @staticmethod
    def select_sources(
        query: str,
        intent: EducationalIntent,
        difficulty: DifficultyLevel,
        source_strategy: Optional[SourceStrategy] = None,
        doc_mode: Optional[DocumentUsageMode] = None,
    ) -> Tuple[List[SourceType], str]:
        q_lower = query.lower()
        sources: List[SourceType] = []
        reasons: List[str] = []

        if source_strategy is None:
            source_strategy, _ = RuleBasedPlannerEngine.determine_source_strategy(query, intent, [])

        if doc_mode is None:
            doc_mode, _ = RuleBasedPlannerEngine.determine_document_usage_mode(query, intent)

        # 1. Base sources according to document usage mode & strategy
        if doc_mode == DocumentUsageMode.REQUIRED:
            if source_strategy == SourceStrategy.DOCUMENT_ONLY:
                sources = [SourceType.INTERNAL_DOCUMENT]
                reasons.append("Selected internal documents exclusively for explicit document query.")
            else:
                sources = [SourceType.INTERNAL_DOCUMENT, SourceType.GENERAL_AI, SourceType.WIKIPEDIA]
                reasons.append("Selected internal documents augmented with external sources.")
        elif doc_mode == DocumentUsageMode.PREFERRED:
            sources = [SourceType.INTERNAL_DOCUMENT, SourceType.GENERAL_AI, SourceType.WIKIPEDIA]
            reasons.append("Selected internal documents alongside external knowledge for topic overlap.")
        else:
            if source_strategy == SourceStrategy.GENERAL_KNOWLEDGE:
                sources = [SourceType.GENERAL_AI, SourceType.WIKIPEDIA]
                reasons.append("Selected General AI and Wikipedia for general educational query.")
            elif source_strategy == SourceStrategy.RESEARCH:
                sources = [SourceType.GENERAL_AI, SourceType.SEMANTIC_SCHOLAR, SourceType.ARXIV, SourceType.TRUSTED_WEB]
                reasons.append("Selected Semantic Scholar, arXiv, Trusted Web, and General AI for research query.")
            elif source_strategy == SourceStrategy.WEB_AUGMENTED:
                sources = [SourceType.GENERAL_AI, SourceType.TRUSTED_WEB, SourceType.WIKIPEDIA]
                reasons.append("Selected Trusted Web and Wikipedia.")
            else:
                sources = [SourceType.GENERAL_AI, SourceType.WIKIPEDIA]
                reasons.append("Selected General AI and Wikipedia.")

        # 2. Explicit resource-seeking additions with whole-word boundary checks
        explicit_video = intent == EducationalIntent.VIDEO_RECOMMENDATION or any(
            re.search(r'\b' + re.escape(w) + r'\b', q_lower) for w in ["video", "videos", "youtube", "watch", "tutorial video", "video lecture", "youtube videos"]
        )
        if explicit_video:
            if SourceType.VIDEO not in sources:
                sources.append(SourceType.VIDEO)
                reasons.append("Added YouTube for video recommendations.")
            if SourceType.TRUSTED_WEB not in sources:
                sources.append(SourceType.TRUSTED_WEB)
                reasons.append("Added Trusted Web for video search fallback.")

        explicit_book = intent == EducationalIntent.BOOK_RECOMMENDATION or any(
            re.search(r'\b' + re.escape(w) + r'\b', q_lower) for w in ["book", "books", "textbook", "reading list", "recommended books"]
        )
        if explicit_book:
            if SourceType.BOOK not in sources:
                sources.append(SourceType.BOOK)
                reasons.append("Added Google Books for literature recommendations.")
            if SourceType.TRUSTED_WEB not in sources:
                sources.append(SourceType.TRUSTED_WEB)

        explicit_github = intent in (EducationalIntent.PROGRAMMING_HELP, EducationalIntent.CODE_RESOURCE_RECOMMENDATION) or any(
            re.search(r'\b' + re.escape(w) + r'\b', q_lower) for w in ["github", "repo", "repos", "repository", "repositories", "open source project"]
        )
        if explicit_github:
            if SourceType.GITHUB_REPO not in sources:
                sources.append(SourceType.GITHUB_REPO)
                reasons.append("Added GitHub for repository search.")
            if SourceType.TRUSTED_WEB not in sources:
                sources.append(SourceType.TRUSTED_WEB)

        explicit_research = intent in (EducationalIntent.RESEARCH, EducationalIntent.RESEARCH_DISCOVERY) or any(
            re.search(r'\b' + re.escape(w) + r'\b', q_lower) for w in ["paper", "papers", "arxiv", "semantic scholar", "academic paper", "research paper", "research papers"]
        )
        if explicit_research:
            if SourceType.ARXIV not in sources:
                sources.append(SourceType.ARXIV)
            if SourceType.SEMANTIC_SCHOLAR not in sources:
                sources.append(SourceType.SEMANTIC_SCHOLAR)
            if SourceType.TRUSTED_WEB not in sources:
                sources.append(SourceType.TRUSTED_WEB)
            reasons.append("Added arXiv and Semantic Scholar for research papers.")

        unique_sources = []
        for s in sources:
            if s not in unique_sources:
                unique_sources.append(s)

        return unique_sources, " ".join(reasons)

    @staticmethod
    def determine_retrieval_strategy(selected_sources: List[SourceType]) -> Tuple[RetrievalStrategy, str]:
        if set(selected_sources) == {SourceType.INTERNAL_DOCUMENT}:
            return RetrievalStrategy.INTERNAL_ONLY, "Strategy set to Internal Only for document-grounded query."
        if SourceType.SEMANTIC_SCHOLAR in selected_sources or SourceType.ARXIV in selected_sources:
            return RetrievalStrategy.RESEARCH, "Strategy set to Research for academic paper discovery."
        if SourceType.VIDEO in selected_sources or SourceType.BOOK in selected_sources or SourceType.WIKIPEDIA in selected_sources:
            return RetrievalStrategy.EDUCATIONAL, "Strategy set to Educational for multi-media learning."
        if SourceType.INTERNAL_DOCUMENT in selected_sources and any(s in selected_sources for s in [SourceType.TRUSTED_WEB, SourceType.WIKIPEDIA, SourceType.GENERAL_AI]):
            return RetrievalStrategy.HYBRID, "Strategy set to Hybrid for document + external evidence."

        return RetrievalStrategy.EDUCATIONAL, "Default educational retrieval strategy."

    @staticmethod
    def determine_expected_output(intent: EducationalIntent) -> ExpectedOutputFormat:
        mapping = {
            EducationalIntent.COMPARISON: ExpectedOutputFormat.COMPARISON_TABLE,
            EducationalIntent.RESEARCH: ExpectedOutputFormat.RESEARCH_SURVEY,
            EducationalIntent.RESEARCH_DISCOVERY: ExpectedOutputFormat.RESEARCH_SURVEY,
            EducationalIntent.QUIZ_GENERATION: ExpectedOutputFormat.QUIZ,
            EducationalIntent.FLASHCARDS: ExpectedOutputFormat.FLASHCARDS,
            EducationalIntent.ROADMAP: ExpectedOutputFormat.LEARNING_ROADMAP,
            EducationalIntent.PROGRAMMING_HELP: ExpectedOutputFormat.CODE_WALKTHROUGH,
            EducationalIntent.CODE_RESOURCE_RECOMMENDATION: ExpectedOutputFormat.CODE_WALKTHROUGH,
            EducationalIntent.BOOK_RECOMMENDATION: ExpectedOutputFormat.BOOK_LIST,
            EducationalIntent.VIDEO_RECOMMENDATION: ExpectedOutputFormat.VIDEO_RECOMMENDATIONS,
            EducationalIntent.STUDY_NOTES: ExpectedOutputFormat.STUDY_NOTES,
            EducationalIntent.DOCUMENT_QUERY: ExpectedOutputFormat.STUDY_NOTES,
            EducationalIntent.TOPIC_SUMMARY: ExpectedOutputFormat.SUMMARY,
        }
        return mapping.get(intent, ExpectedOutputFormat.DETAILED_EXPLANATION)

    @classmethod
    def generate_plan(
        cls,
        query: str,
        history: List[Dict[str, Any]] = None,
        available_docs: Optional[List[str]] = None
    ) -> ExecutionPlan:
        history = history or []
        reasoning_steps = []

        target_docs = cls.resolve_target_documents(query, available_docs)
        if target_docs:
            reasoning_steps.append(f"Target Documents Resolved: {target_docs}")

        intent, intent_reason = cls.classify_intent(query, history)
        reasoning_steps.append(f"Intent Classification: '{intent.value}' — {intent_reason}")

        secondary_intents: List[EducationalIntent] = []
        norm_q = cls.normalize_query(query)
        if (" and show me " in norm_q or " show me " in norm_q) and ("github" in norm_q or "implementation" in norm_q):
            if intent != EducationalIntent.CODE_RESOURCE_RECOMMENDATION:
                secondary_intents.append(EducationalIntent.CODE_RESOURCE_RECOMMENDATION)
            elif intent == EducationalIntent.CODE_RESOURCE_RECOMMENDATION and any(w in norm_q for w in ["explain", "overview"]):
                intent = EducationalIntent.CONCEPT_EXPLANATION
                secondary_intents.append(EducationalIntent.CODE_RESOURCE_RECOMMENDATION)

        if (" and show me " in norm_q or " show me " in norm_q) and any(w in norm_q for w in ["paper", "papers", "research"]):
            if intent != EducationalIntent.RESEARCH_DISCOVERY:
                secondary_intents.append(EducationalIntent.RESEARCH_DISCOVERY)

        if " and quiz me" in norm_q or " and test me" in norm_q or " quiz me " in norm_q:
            if intent not in (EducationalIntent.QUIZ_GENERATION, EducationalIntent.PRACTICE_QUIZ):
                secondary_intents.append(EducationalIntent.QUIZ_GENERATION)

        if secondary_intents:
            reasoning_steps.append(f"Secondary Intents Detected: {[s.value for s in secondary_intents]}")

        difficulty, diff_reason = cls.estimate_difficulty(query, history, intent)
        reasoning_steps.append(f"Difficulty Estimation: '{difficulty.value}' — {diff_reason}")

        doc_mode, doc_mode_reason = cls.determine_document_usage_mode(query, intent, target_docs, available_docs=available_docs)
        reasoning_steps.append(f"Document Usage Mode: '{doc_mode.value}' — {doc_mode_reason}")

        source_strat, strat_reason = cls.determine_source_strategy(query, intent, history, target_docs=target_docs)
        reasoning_steps.append(f"Source Strategy Selection: '{source_strat.value}' — {strat_reason}")

        selected_sources, source_reason = cls.select_sources(query, intent, difficulty, source_strat, doc_mode=doc_mode)

        # Merge sources for secondary intents
        for sec in secondary_intents:
            sec_sources, _ = cls.select_sources(query, sec, difficulty, source_strat, doc_mode=doc_mode)
            for s in sec_sources:
                if s not in selected_sources:
                    selected_sources.append(s)

        reasoning_steps.append(f"Knowledge Source Selection: {[s.value for s in selected_sources]} — {source_reason}")

        strategy, rstrat_reason = cls.determine_retrieval_strategy(selected_sources)
        reasoning_steps.append(f"Retrieval Strategy: '{strategy.value}' — {rstrat_reason}")

        output_format = cls.determine_expected_output(intent)
        reasoning_steps.append(f"Expected Output Format: '{output_format.value}'")

        est_latency = LatencyEstimate.HIGH if len(selected_sources) >= 4 else (LatencyEstimate.MEDIUM if len(selected_sources) >= 2 else LatencyEstimate.LOW)
        est_cost = CostEstimate.HIGH if SourceType.SEMANTIC_SCHOLAR in selected_sources else CostEstimate.LOW

        requires_internal = SourceType.INTERNAL_DOCUMENT in selected_sources and doc_mode != DocumentUsageMode.EXCLUDED
        requires_external = any(s in selected_sources for s in [SourceType.TRUSTED_WEB, SourceType.WIKIPEDIA])
        requires_research = any(s in selected_sources for s in [SourceType.SEMANTIC_SCHOLAR, SourceType.ARXIV])
        requires_books = SourceType.BOOK in selected_sources
        requires_videos = SourceType.VIDEO in selected_sources
        requires_code = SourceType.GITHUB_REPO in selected_sources

        summary_reasoning = f"Plan for '{query[:40]}...': Intent={intent.value}, SecondaryIntents={[s.value for s in secondary_intents]}, DocMode={doc_mode.value}, SourceStrategy={source_strat.value}, TargetDocs={target_docs}, Sources={[s.value for s in selected_sources]}."

        return ExecutionPlan(
            intent=intent,
            secondary_intents=secondary_intents,
            difficulty=difficulty,
            source_strategy=source_strat,
            document_usage_mode=doc_mode,
            selected_sources=selected_sources,
            retrieval_strategy=strategy,
            expected_output=output_format,
            estimated_latency=est_latency,
            estimated_cost=est_cost,
            reasoning=summary_reasoning,
            reasoning_steps=reasoning_steps,
            requires_internal_documents=requires_internal,
            requires_external_search=requires_external,
            requires_research=requires_research,
            requires_books=requires_books,
            requires_videos=requires_videos,
            requires_code=requires_code,
            target_documents=target_docs,
            metadata={"query": query, "history_len": len(history)},
        )

