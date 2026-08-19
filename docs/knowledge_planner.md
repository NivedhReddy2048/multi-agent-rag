# EKIP Phase 2.2 — Knowledge Planner & LangGraph Orchestration Specification

> **Module**: `core/planner` & `graph/`  
> **Version**: EKIP Phase 2.2 — Intelligence & Planning Layer  
> **Execution Constraint**: Zero-Network / Zero-Retrieval Planning Engine  

---

## 1. Overview & Architecture

Phase 2.2 introduces the **Knowledge Planner Agent** and **LangGraph Planning Graph** to EKIP.

Instead of immediately triggering document or web searches, EKIP first routes every student query through a deterministic planning graph to produce a structured, explainable **`ExecutionPlan`**.

```
Student Query
     │
     ▼
[ LangGraph Planning Graph ]
     ├─► Intent Node (Classifies 15 educational intents)
     ├─► Difficulty Node (Beginner / Intermediate / Advanced / Research)
     ├─► Source Selection Node (AI, Docs, Wiki, arXiv, Scholar, YouTube, Books, GitHub)
     ├─► Retrieval Strategy Node (Internal Only / External Only / Hybrid / Research / Educational)
     ├─► Output Planning Node (Explanation / Survey / Comparison / Quiz / Notes / Video List)
     └─► Execution Plan Node (Compiles ExecutionPlan & flags)
     │
     ▼
[ Structured ExecutionPlan Contract ]
     │
     ▼ (Phase 2.3 execution by retrieval agents)
```

---

## 2. LangGraph Planning Nodes (`graph/nodes/planning_nodes.py`)

The graph executes 6 sequential state transitions without making any network or API calls:

1. **`intent_node`**: Classifies question intent (`concept_explanation`, `topic_summary`, `comparison`, `research`, `video_recommendation`, `book_recommendation`, `quiz_generation`, `programming_help`, `roadmap`, etc.).
2. **`difficulty_node`**: Evaluates complexity (`beginner`, `intermediate`, `advanced`, `research`) based on technical vocabulary and student conversation history length.
3. **`source_selection_node`**: Selects target knowledge sources (`general_ai`, `internal_document`, `wikipedia`, `semantic_scholar`, `arxiv`, `google_books`, `youtube`, `github_repo`).
4. **`retrieval_strategy_node`**: Determines macro strategy (`internal_only`, `external_only`, `hybrid`, `research`, `educational`).
5. **`output_planning_node`**: Determines desired output format (`detailed_explanation`, `comparison_table`, `summary`, `research_survey`, `quiz`, `flashcards`, `learning_roadmap`, etc.).
6. **`execution_plan_node`**: Compiles final `ExecutionPlan` contract and sets resource requirement flags (`requires_internal_documents`, `requires_research`, `requires_videos`, etc.).

---

## 3. `ExecutionPlan` Contract Schema (`core/planner/execution_plan.py`)

```python
class ExecutionPlan(BaseModel):
    intent: EducationalIntent
    difficulty: DifficultyLevel
    selected_sources: List[SourceType]
    retrieval_strategy: RetrievalStrategy
    expected_output: ExpectedOutputFormat
    estimated_latency: LatencyEstimate
    estimated_cost: CostEstimate

    reasoning: str
    reasoning_steps: List[str]

    requires_internal_documents: bool
    requires_external_search: bool
    requires_research: bool
    requires_books: bool
    requires_videos: bool
    requires_code: bool
    metadata: Dict[str, Any]
```

---

## 4. Rule Engine Logic (`core/planner/rules.py`)

The planner operates deterministically without LLM network dependency:

| Trigger Keywords | Classified Intent | Selected Sources | Strategy |
| :--- | :--- | :--- | :--- |
| `paper`, `arxiv`, `research`, `journal` | `research` | `semantic_scholar`, `arxiv`, `trusted_web` | `research` |
| `compare`, `vs`, `difference` | `comparison` | `general_ai`, `wikipedia` | `educational` |
| `video`, `youtube`, `lecture` | `video_recommendation` | `youtube`, `general_ai` | `educational` |
| `book`, `reading list`, `textbook` | `book_recommendation` | `google_books`, `general_ai` | `educational` |
| `uploaded`, `my notes`, `indexed` | `study_notes` | `internal_document`, `general_ai` | `internal_only` |
| `code`, `python`, `github`, `script` | `programming_help` | `github_repo`, `general_ai` | `educational` |

---

## 5. Telemetry & Memory Integration

Planning decisions are logged automatically to SQLite via `ConversationMemory.record_planner_telemetry()`:
- `planner_intent`
- `planner_difficulty`
- `planner_sources`
- `planner_strategy`
- `estimated_latency`
- `estimated_cost`

---

## 6. Downstream Phase 2.3 Integration Roadmap

In Phase 2.3, downstream retrieval agents will consume the generated `ExecutionPlan`:
- If `requires_research` is True → Fan-out to `SemanticScholarProvider` & `ArxivProvider`.
- If `requires_videos` is True → Fan-out to `YoutubeProvider`.
- If `requires_books` is True → Fan-out to `GoogleBooksProvider`.
- If `requires_internal_documents` is True → Query local Vector DB & BM25 hybrid retrieval engine.
