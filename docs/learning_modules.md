# EKIP Phase 2.7 — Intelligent Learning Modules & Adaptive Study Assistant Specification

> **Module**: `core/workspace/modules/`, `docs/learning_modules.md`  
> **Version**: EKIP Phase 2.7 — Adaptive Learning Plugin Ecosystem  

---

## 1. Architectural Philosophy & Ecosystem Flow

Following your explicit architectural recommendation, **the core 12-node LangGraph pipeline is kept completely stable and untouched**.

All educational plugins consume `EducationalResponse` as downstream processors:

```
                  [ EducationalResponse ]
                             │
     ┌───────────────────────┼───────────────────────┐
     │                       │                       │
     ▼                       ▼                       ▼
 Flashcards              Quiz Engine             Mind Maps
 (6 Card Types)       (5 Question Types)      (Tree & Graphs)
     │                       │                       │
     ├───────────────────────┼───────────────────────┤
     ▼                       ▼                       ▼
Revision Assistant     Interview Prep        Coding Practice
(Cheat Sheets)        (Qs & Rubrics)        (Complexity & Solutions)
     │                       │                       │
     └───────────────────────┼───────────────────────┘
                             │
                             ▼
                  [ Research Assistant ]
                             │
                             ▼
                [ Student Workspace DB ]
```

---

## 2. Component Breakdown

### 2.1 `LearningModuleManager` (`core/workspace/modules/module_manager.py`)
- Plugin registry discovering, enabling/disabling, registering, and executing modules dynamically.
- `execute_all(response)` runs all enabled modules sequentially.

### 2.2 `AdaptiveDifficultyEngine` (`core/workspace/modules/adaptive_engine.py`)
- Dynamically estimates student current knowledge level (`beginner`, `intermediate`, `advanced`) based on `EducationalResponse` mode and workspace history.

### 2.3 Registered Learning Modules
1. **Enhanced Flashcard Module (`FlashcardModule`)**: Supports 6 card formats (`definition`, `concept`, `true_false`, `fill_in_the_blank`, `image_placeholder`, `reverse_card`) across 3 difficulty tiers.
2. **Advanced Quiz Engine (`QuizGeneratorModule`)**: Supports 5 question formats (`MCQ`, `True/False`, `Multiple Select`, `Short Answer`, `Scenario`) with automated answer explanations.
3. **Mind Map Generator (`MindMapModule`)**: Produces structured JSON tree hierarchies.
4. **Concept Relationship Graph (`ConceptGraphModule`)**: Connects prerequisites, applications, and related topics into node/edge graph structures.
5. **Revision Assistant (`RevisionAssistantModule`)**: Produces one-page revision sheets, exam cheat sheets, and formula reference sheets.
6. **Interview Preparation Module (`InterviewPrepModule`)**: Generates technical interview questions, sample answer keys, deep-dive probes, and evaluation rubrics.
7. **Coding Practice Module (`CodingPracticeModule`)**: Generates Python coding exercises, test edge cases, sample code, and time/space complexity analysis.
8. **Research Assistant Module (`ResearchAssistantModule`)**: Produces literature summaries, research gap analysis, future research directions, and comparison tables.

---

## 3. Telemetry & Analytics (`query_analytics`)

Tracked via `ConversationMemory.record_module_telemetry()`:
- `flashcards_generated`
- `quiz_attempts`
- `avg_quiz_score`
- `revision_usage`
- `interview_practice`
- `coding_exercises`
- `module_execution_latency`
