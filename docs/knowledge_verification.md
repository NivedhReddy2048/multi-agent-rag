# EKIP Phase 2.4 — Knowledge Verification, Ranking & Evidence Intelligence Specification

> **Module**: `core/verification/`, `core/models/verification.py`, `graph/nodes/verification_node.py`  
> **Version**: EKIP Phase 2.4 — Evidence Intelligence Layer  

---

## 1. Overview & Architecture

Phase 2.4 introduces the **Knowledge Intelligence & Verification Layer** for EKIP. 

Rather than generating an immediate synthesis or merged answer, EKIP evaluates evidence quality, cross-source corroboration, conflict detection, duplicate detection, and source credibility across all multi-source outputs collected in Phase 2.3.

```
Student Query
     │
     ▼
[ LangGraph Planning Graph ] (Phase 2.2)
     │
     ▼
[ Parallel Knowledge Collection ] (Phase 2.3)
     │
     ▼
[ KnowledgeCollection Contract ]
     │
     ▼
[ Knowledge Verification Node ] (Phase 2.4)
     ├─► 1. Base Credibility Scoring
     ├─► 2. Query Relevance & Completeness Evaluation
     ├─► 3. Duplicate Detection & Canonical Selection
     ├─► 4. Cross-Source Agreement & Conflict Detection
     ├─► 5. Freshness Evaluation
     └─► 6. Multi-Source Enhanced CRAG Grading (CORRECT / AMBIGUOUS / INCORRECT)
     │
     ▼
[ Evidence Ranking Node ] ──► Rank evidence by multi-dimensional VerificationProfile
     │
     ▼
[ VerifiedKnowledgeCollection Contract ]
     │
     ▼ (Developer Inspection Panel / Input to Phase 2.5 Final Synthesis)
```

---

## 2. Multi-Dimensional Verification Profile (`VerificationProfile`)

To ensure complete explainability and transparency, evidence quality is computed as a 6-dimensional profile rather than a single opaque score:

```python
class VerificationProfile(BaseModel):
    relevance_score: float         # Semantic similarity & query term alignment (25%)
    credibility_score: float       # Base publisher authority weight (25%)
    agreement_score: float         # Cross-source corroboration & consensus (20%)
    freshness_score: float         # Publication recency & timeliness (10%)
    completeness_score: float      # Information depth & length completeness (10%)
    educational_value_score: float # Instructional utility & clarity (10%)
    overall_score: float           # Weighted composite verification score (0-1)
```

---

## 3. Base Credibility Model (`BASE_CREDIBILITY_WEIGHTS`)

Base credibility scores represent prior trust levels for each knowledge source:

| Source Type | Category | Base Weight | Rationale |
| :--- | :--- | :--- | :--- |
| `SEMANTIC_SCHOLAR` | Academic Literature | **0.95** | Peer-reviewed academic journals & papers |
| `ARXIV` | Academic Preprints | **0.90** | Open scientific research preprints |
| `BOOK` / `GOOGLE_BOOKS` | Textbooks | **0.90** | Published textbooks & reference books |
| `INTERNAL_DOCUMENT` | Uploaded Docs | **0.85** | Enterprise / student uploaded materials |
| `WIKIPEDIA` | Reference | **0.85** | Open community encyclopedic summaries |
| `GITHUB_REPO` | Open-Source | **0.80** | Executable code repositories |
| `TRUSTED_WEB` | Web Search | **0.75** | Live web search snippets (Tavily/DDG) |
| `VIDEO` | Educational Video | **0.70** | Video lecture tutorials |
| `GENERAL_AI` | Multi-LLM | **0.65** | Baseline reasoning (supporting explanation) |

---

## 4. Enhanced CRAG Verifier (`EnhancedCRAGVerifier`)

Extends traditional single-document CRAG into a multi-source evidence sufficiency evaluator:

- **`CORRECT`** (Sufficiency Score ≥ 0.70): High multi-source coverage & agreement.
- **`AMBIGUOUS`** (0.35 ≤ Sufficiency Score < 0.70): Partial evidence coverage.
- **`INCORRECT`** (Sufficiency Score < 0.35): Insufficient multi-source coverage.

---

## 5. Duplicate & Conflict Detection

- **Duplicate Detection**: Groups items with text similarity ratio ≥ 0.75, designates 1 canonical result (`is_canonical=True`), and tracks non-canonical items under `duplicate_group`.
- **Conflict Detection**: Compares key claims and negation indicators across source pairs. Conflicts are flagged explicitly in `conflicts` without automatic resolution.

---

## 6. Telemetry & Analytics (`query_analytics`)

Recorded via `ConversationMemory.record_verification_telemetry()`:
- `verification_score`
- `agreement_score`
- `conflict_count`
- `duplicate_count`
- `ranking_latency`
- `verification_latency`

---

## 7. Roadmap to Phase 2.5 (Final Educational Synthesis & Output Planning)

The output of Phase 2.4 (`VerifiedKnowledgeCollection`) serves as the input for Phase 2.5:
1. Selecting top canonical evidence based on intent-specific priorities.
2. Generating tailored educational outputs (Detailed Explanations, Flashcards, Mindmaps, Quizzes).
3. Maintaining zero-hallucination source attribution grounded in verified evidence.
