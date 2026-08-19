# EKIP Phase 2.5 — Knowledge Synthesis, Educational Response Generation & Guided Learning Specification

> **Module**: `core/synthesis/`, `core/models/synthesis.py`, `graph/nodes/synthesis_node.py`, `graph/nodes/guided_learning_node.py`  
> **Version**: EKIP Phase 2.5 — Educational Synthesis & Guided Learning Engine  

---

## 1. Overview & Core Architecture

Phase 2.5 transforms EKIP from a verification engine into an active, evidence-driven **Educational Learning Platform**.

Following clean architectural practices, responsibility is split between evidence processing and user presentation:

```
[ VerifiedKnowledgeCollection ] (Phase 2.4)
               │
               ▼
   [ Knowledge Synthesizer ]  <── Core Evidence Understanding & Claim Fusion
               │
      [ SynthesizedKnowledge ]
               │
               ▼
      [ Response Composer ]    <── Educational Layout, Formatting & Provenance
               │
     [ EducationalResponse ]
               │
               ▼
    [ Guided Learning Engine ] <── Follow-Up Questions & Learning Path Generation
               │
               ▼
[ LangGraph StateGraph (11 Nodes) ] ──► Layered Streamlit UI Render
```

---

## 2. Component Breakdown

### 2.1 `KnowledgeSynthesizer` (`core/synthesis/knowledge_synthesizer.py`)
- Fuses canonical and supporting evidence.
- Respects evidence quality (primary canonical results drive the main explanation, supporting results populate secondary excerpts).
- Explicitly flags conflicting views without silently merging contradictory claims.

### 2.2 `ResponseComposer` (`core/synthesis/response_composer.py`)
- Formats synthesized knowledge into the 12-section `EducationalResponse` container.
- Categorizes evidence into domain layers: `uploaded_notes`, `trusted_web`, `wikipedia`, `research`, `books`, `videos`, `code_examples`.
- Attaches citation tags `[Source #]` and provider provenance metadata.

### 2.3 `EducationalPromptBuilder` (`core/synthesis/prompt_builder.py`)
- Formats structured LLM prompts containing learner difficulty, educational intent, requested format, and indexed evidence blocks.

### 2.4 `GuidedLearningEngine` (`core/synthesis/guided_learning.py`)
- Generates 3 context-aware, non-generic follow-up questions tailored to topic and intent.
- Generates a 4-tier structured learning path: `Prerequisites` ➔ `Current Topic` ➔ `Next Topics` ➔ `Advanced Topics`.

---

## 3. Educational Response Model (`EducationalResponse`)

```python
class EducationalResponse(BaseModel):
    query: str
    educational_mode: str
    ai_explanation: str
    uploaded_notes: List[Dict[str, Any]]
    trusted_web: List[Dict[str, Any]]
    wikipedia: List[Dict[str, Any]]
    research: List[Dict[str, Any]]
    books: List[Dict[str, Any]]
    videos: List[Dict[str, Any]]
    code_examples: List[Dict[str, Any]]
    key_takeaways: List[str]
    important_terms: Dict[str, str]
    learning_summary: str
    conflicts: List[Dict[str, Any]]
    guided_questions: List[str]
    learning_path: Optional[LearningPath]
    citations: List[Dict[str, Any]]
    providers_used: List[str]
    confidence: float
    agreement: float
```

---

## 4. LangGraph 11-Node Sequence

```
START -> intent -> difficulty -> source_selection -> retrieval_strategy -> output_planning -> execution_plan -> knowledge_collection -> knowledge_verification -> evidence_ranking -> knowledge_synthesis -> guided_learning -> END
```

---

## 5. Telemetry & Analytics (`query_analytics`)

Tracked via `ConversationMemory.record_synthesis_telemetry()`:
- `synthesis_latency`
- `educational_mode`
- `guided_questions_generated`
- `learning_path_generated`
