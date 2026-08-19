"""Unit and Integration Test Suite for EKIP Phase 2.6 Student Workspace, Learning Sessions & Library."""

import pytest
import os
import tempfile
from core.models.synthesis import EducationalResponse, LearningPath
from core.models.workspace import LearningSession, Notebook, StudyNote, Bookmark, StudyCollection
from core.workspace import WorkspaceManager, ExportEngine, FlashcardModule, QuizGeneratorModule, RevisionNotesModule
from graph.builder import create_ekip_planning_graph
from graph.state import EKIPGraphState


@pytest.fixture
def tmp_workspace():
    """Build temporary WorkspaceManager with isolated SQLite DB."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        db_path = os.path.join(tmp_dir, "test_workspace.db")
        mgr = WorkspaceManager(db_path=db_path)
        yield mgr


def test_session_management(tmp_workspace):
    """Verify creation and retrieval of persistent learning sessions."""
    sess = tmp_workspace.create_session("AI Fundamentals", "Studying Machine Learning principles", ["AI", "ML"])
    assert sess.title == "AI Fundamentals"

    sessions = tmp_workspace.list_sessions()
    assert len(sessions) == 1
    assert sessions[0].id == sess.id


def test_notebook_and_study_notes(tmp_workspace):
    """Verify notebook creation, study note saving, and notebook note retrieval."""
    nb = tmp_workspace.create_notebook("Neural Networks", "Deep learning study notes")
    assert nb.title == "Neural Networks"

    note = tmp_workspace.save_study_note(
        query="What is Backpropagation?",
        title="Backpropagation Notes",
        ai_explanation="Backpropagation calculates gradients through hidden layers.",
        notebook_id=nb.id,
        key_takeaways=["Calculates gradients using chain rule"],
        important_terms={"Gradient": "Vector of partial derivatives"},
    )
    assert note.id != ""

    notebooks = tmp_workspace.list_notebooks()
    assert len(notebooks) == 1
    assert len(notebooks[0].notes) == 1
    assert notebooks[0].notes[0].title == "Backpropagation Notes"


def test_bookmark_management(tmp_workspace):
    """Verify bookmark creation, listing, and read state toggling."""
    bm = tmp_workspace.add_bookmark("Attention is All You Need", "paper", "https://arxiv.org/abs/1706.03762")
    assert bm.is_read is False

    bms = tmp_workspace.list_bookmarks()
    assert len(bms) == 1

    tmp_workspace.toggle_bookmark_read(bm.id)
    bms_updated = tmp_workspace.list_bookmarks()
    assert bms_updated[0].is_read is True


def test_smart_search(tmp_workspace):
    """Verify local smart search across saved notes, notebooks, and bookmarks."""
    tmp_workspace.create_notebook("Quantum Computing", "Qubits and superposition")
    tmp_workspace.save_study_note("Quantum Qubit", "Qubit Basics", "Qubits exist in superposition.")
    tmp_workspace.add_bookmark("Quantum Shor's Algorithm Paper", "paper", "https://example.com/shor")

    res = tmp_workspace.smart_search("Quantum")

    assert len(res["notes"]) >= 1
    assert len(res["notebooks"]) >= 1
    assert len(res["bookmarks"]) >= 1


def test_export_engine():
    """Verify ExportEngine exports to Markdown, TXT, and DOCX formats."""
    note = StudyNote(
        id="n101",
        query="What is RAG?",
        title="RAG Systems Note",
        ai_explanation="Retrieval-Augmented Generation combines retrieval with LLM synthesis.",
        key_takeaways=["Reduces hallucinations"],
        important_terms={"RAG": "Retrieval-Augmented Generation"},
    )
    exporter = ExportEngine()

    md = exporter.export_to_markdown(note)
    txt = exporter.export_to_txt(note)
    docx_bytes = exporter.export_to_docx(note)

    assert "# RAG Systems Note" in md
    assert "TITLE: RAG Systems Note" in txt
    assert isinstance(docx_bytes, bytes)
    assert len(docx_bytes) > 0


def test_plugin_learning_modules():
    """Verify execution of FlashcardModule, QuizGeneratorModule, and RevisionNotesModule plugins."""
    resp = EducationalResponse(
        query="Neural Networks",
        ai_explanation="Neural networks are composed of artificial neurons.",
        key_takeaways=["Uses activation functions", "Trained via backpropagation"],
        important_terms={"Neuron": "Basic processing unit of neural network"},
    )

    fc_mod = FlashcardModule()
    fc_res = fc_mod.process(resp)
    assert fc_res["flashcard_count"] >= 1
    assert fc_res["flashcards"][0]["type"] == "definition"

    quiz_mod = QuizGeneratorModule()
    quiz_res = quiz_mod.process(resp)
    assert quiz_res["total_questions"] >= 1

    rev_mod = RevisionNotesModule()
    rev_res = rev_mod.process(resp)
    assert len(rev_res["last_minute_revision"]) >= 1



def test_full_langgraph_12_node_workspace_pipeline():
    """Verify full 12-node LangGraph execution including workspace persistence node."""
    graph = create_ekip_planning_graph()
    state = graph.invoke({"question": "Explain Neural Networks and Backpropagation"})

    assert isinstance(state, EKIPGraphState)
    assert "workspace_saved_note_id" in state.provider_metadata
    assert state.provider_metadata["workspace_saved_note_id"] != ""
