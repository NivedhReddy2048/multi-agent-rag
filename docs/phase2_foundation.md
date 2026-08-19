# EKIP Phase 2.1 — Foundation Migration Specification

> **Platform**: Educational Knowledge Intelligence Platform (EKIP)  
> **Phase**: 2.1 — Foundation Migration & Architecture Preparation  
> **Status**: Completed & Verified  

---

## 1. Executive Summary & New Platform Vision

EKIP is evolving from an *Enterprise Knowledge Intelligence Platform* into an **Educational Knowledge Intelligence Platform (EKIP)**.

### Motto & Identity
- **New Motto**: *"Learn from Multiple Trusted Knowledge Sources — Your AI Learning Companion"*
- **Core Value Proposition**: *One Student Question → Intent Analysis & Source Planning → Multi-Domain Knowledge Collection → Quality & Factuality Verification → Unified Consensus Summary + Guided Learning Recommendations.*

---

## 2. Phase 2.1 Scope & Non-Negotiable System Boundaries

Phase 2.1 is strictly a **foundation migration and architecture preparation**.

### Preserved Subsystems (Zero Breaking Changes)
1. **Hybrid Retrieval Pipeline**: BM25 + Vector Search + RRF + Cross-Encoder Reranking remain 100% untouched for document chat queries.
2. **Corrective RAG (CRAG)**: Web fallback logic and hallucination evaluation remain untouched.
3. **Multi-LLM Failover**: Primary Gemini -> Groq -> Cohere -> Mistral failover mechanism operates as designed.
4. **Conversation Memory**: SQLite storage persists messages, feedback, and session state seamlessly.
5. **Analytics & Telemetry**: Performance metrics, query counts, and latency tracking remain intact.
6. **Query-Time API Guard**: New external APIs (Firecrawl, Jina AI, Semantic Scholar, arXiv, Wikipedia, YouTube, Google Books) are **registered and audited in diagnostics** but are **NOT invoked during live user queries** in Phase 2.1.

---

## 3. Foundation Architectural Components Created

### A. Provider Registry (`core/providers/`)
Central singleton managing 14 knowledge providers across 6 domain categories:
- **General AI**: Gemini, Groq, Cohere, Mistral
- **Web Search**: Tavily, DuckDuckGo (SerpApi / native DDGS)
- **Content Extraction & Reader**: Firecrawl, Jina AI Reader (`r.jina.ai`)
- **Academic Literature**: Semantic Scholar, arXiv, Wikipedia
- **Educational Media & Books**: YouTube Data API v3, Google Books API v1
- **Repositories & Code**: GitHub REST API v3

### B. LangGraph Preparation Package (`graph/`)
- `graph/state.py`: Defines `EKIPGraphState` with fields for `question`, `intent`, `conversation_history`, `retrieved_documents`, `retrieved_web`, `retrieved_research`, `retrieved_books`, `retrieved_videos`, `retrieved_wikipedia`, `provider_metadata`, `confidence`, `faithfulness`, `final_summary`, and `recommended_questions`.
- `graph/builder.py`: Skeleton StateGraph builder for future orchestration.
- `graph/nodes/` & `graph/edges/`: Module placeholders.

### C. Educational Domain Models (`core/models/`)
Reusable Pydantic models:
- `KnowledgeSource`, `KnowledgeResult`, `LearningResource`
- `ResearchPaper`, `BookRecommendation`, `VideoRecommendation`
- `LearningSummary`, `RecommendedQuestion`

### D. Planner & Processing Interfaces (`core/interfaces/`)
Abstract classes defining future execution signatures:
- `KnowledgePlanner.plan(question)`
- `KnowledgeRouter.route_and_collect(question, sources)`
- `KnowledgeVerifier.verify(query, results)`
- `KnowledgeRanker.rank(query, verified)`
- `LearningSummarizer.summarize(query, evidence)`

---

## 4. UI & Navigation Enhancements

1. **Rebranded Header & Navigation**:
   - Educational Knowledge Companion title and motto.
   - Preserved 4 core tabs: `💬 Chat`, `📊 Analytics`, `📚 Documents`, `🩺 LLM Health & Diagnostics`.

2. **Educational Quick Action Starters**:
   - 📘 Explain a Concept
   - 📄 Summarize My Notes
   - 📚 Compare Two Topics
   - 🔬 Find Research Papers
   - 🌐 Explore Trusted Sources
   - 🎥 Recommend Videos
   - 📝 Create Study Notes
   - ❓ Practice Quiz

3. **Categorized Diagnostics Matrix**:
   - Providers grouped into expandable categories (General AI, Search, Extraction, Academic, Media/Books, Repositories).
   - Unused providers cleanly display `Configured (Ready)` or `Public Open Access` with masked secret keys.

---

## 5. Future Development Phases

- **Phase 2.2 — Knowledge Planner & Intent Router**: Implement `KnowledgePlanner` logic using LangGraph nodes to dynamically route questions based on semantic intent.
- **Phase 2.3 — Cross-Source Quality Verification & Synthesis**: Implement `KnowledgeVerifier` and `LearningSummarizer` to merge cross-source evidence into unified learning guides.
- **Phase 2.4 — Multi-Domain Educational Workspace UI**: Add multi-tab views for research papers, video lectures, book previews, and interactive quizzes.
