# EKIP Phase 2.6 — Student Workspace, Learning Sessions & Knowledge Library Specification

> **Module**: `core/workspace/`, `core/models/workspace.py`, `graph/nodes/workspace_node.py`  
> **Version**: EKIP Phase 2.6 — Student Workspace Engine  

---

## 1. Overview & Workspace Architecture

Phase 2.6 transforms EKIP into a **complete AI Learning Workspace**. Questions are no longer treated as ephemeral chat exchanges—instead, every interaction becomes part of a persistent learning session, subject notebook, or study library.

```
[ Student Input ]
       │
       ▼
[ LangGraph StateGraph (12 Nodes) ]
  ├── 1–6. Planning Nodes
  ├── 7. Knowledge Collection Node
  ├── 8. Knowledge Verification Node
  ├── 9. Evidence Ranking Node
  ├── 10. Knowledge Synthesis Node
  ├── 11. Guided Learning Node
  └── 12. Workspace Persistence Node
               │
               ▼
   [ Workspace SQLite DB ] (workspace.db)
     ├── learning_sessions
     ├── notebooks
     ├── study_notes
     ├── study_collections
     └── bookmarks
               │
               ▼
[ Student Workspace UI (Sidebar Navigation) ]
  ├── 📚 Subject Notebooks
  ├── 📝 Saved Notes Library & Exports
  ├── 📂 Study Collections
  ├── 🔖 Resource Bookmarks
  ├── 🔍 Smart Workspace Search
  └── 🕒 Sessions & Timeline
```

---

## 2. Plugin Learning Module System (`LearningModule`)

To keep EKIP modular as future educational capabilities are added, Phase 2.6 introduces a plugin extension interface:

```python
class LearningModule(ABC):
    name: str
    description: str

    @abstractmethod
    def process(self, response: EducationalResponse, session: Optional[LearningSession] = None) -> Dict[str, Any]:
        pass
```

### Built-in Enabled Plugins:
1. `FlashcardModule`: Extracts term-definition flashcards for active recall study.
2. `QuizGeneratorModule`: Generates multiple-choice practice quiz questions with answer keys.
3. `RevisionNotesModule`: Condenses explanations into bulleted exam revision cheat sheets.

---

## 3. Storage & Domain Models (`core/models/workspace.py`)

- `LearningSession`: Persistent multi-query study sessions.
- `Notebook`: Subject notebooks organizing related study notes.
- `StudyNote`: Persisted educational responses with key takeaways and glossaries.
- `StudyCollection`: Reusable groupings of papers, videos, books, and study materials.
- `Bookmark`: Saved external references with read/unread tracking.
- `WorkspaceProgress`: Progress metrics tracking total queries, saved notes, and completed topics.

---

## 4. Export Engine (`ExportEngine`)

Supports multi-format exports for offline study:
- **Markdown (`.md`)**: Full structured Markdown export.
- **Plain Text (`.txt`)**: Clean text document export.
- **DOCX (`.docx`)**: Microsoft Word document generated via `python-docx`.

---

## 5. LangGraph 12-Node Workflow

```
START -> intent -> difficulty -> source_selection -> retrieval_strategy -> output_planning -> execution_plan -> knowledge_collection -> knowledge_verification -> evidence_ranking -> knowledge_synthesis -> guided_learning -> workspace_persistence -> END
```
