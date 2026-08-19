"""Unit and Integration Test Suite for EKIP Phase 2.7 Intelligent Learning Modules."""

import pytest
import os
import tempfile
from core.models.synthesis import EducationalResponse, LearningPath
from core.workspace.modules import (
    LearningModuleManager,
    module_manager,
    adaptive_engine,
    FlashcardModule,
    QuizGeneratorModule,
    MindMapModule,
    ConceptGraphModule,
    RevisionAssistantModule,
    InterviewPrepModule,
    CodingPracticeModule,
    ResearchAssistantModule,
)
from core.memory import ConversationMemory
from graph.builder import create_ekip_planning_graph
from graph.state import EKIPGraphState


@pytest.fixture
def sample_edu_response():
    return EducationalResponse(
        query="Machine Learning Principles",
        educational_mode="detailed_explanation",
        ai_explanation="Machine learning involves training algorithms on datasets using loss optimization.",
        key_takeaways=["Loss functions quantify prediction errors", "Gradient descent updates parameters"],
        important_terms={"Gradient Descent": "Optimization algorithm minimizing loss"},
        learning_summary="Machine learning trains parameter models using gradient optimization.",
        confidence=0.94,
        agreement=0.98,
        providers_used=["wikipedia", "arxiv"],
        learning_path=LearningPath(
            prerequisites=["Calculus", "Linear Algebra"],
            next_topics=["Deep Learning"],
            advanced_topics=["Transformer Architectures"],
        ),
    )


def test_module_manager_discovery_and_registration():
    """Verify module discovery, registration, enable/disable, and list capabilities."""
    mgr = LearningModuleManager()
    fc = FlashcardModule()
    mgr.register_module(fc)

    assert len(mgr.list_modules()) == 1
    assert mgr.get_module("flashcards") is not None

    mgr.disable_module("flashcards")
    assert mgr.get_module("flashcards").is_enabled is False

    mgr.enable_module("flashcards")
    assert mgr.get_module("flashcards").is_enabled is True


def test_adaptive_difficulty_engine(sample_edu_response):
    """Verify adaptive difficulty level estimation."""
    diff_beg = adaptive_engine.estimate_difficulty(sample_edu_response, workspace_history_count=0)
    assert diff_beg in ["beginner", "intermediate", "advanced"]

    card_diff = adaptive_engine.map_to_card_difficulty("beginner")
    assert card_diff == "easy"


def test_enhanced_flashcard_module(sample_edu_response):
    """Verify flashcard module generates 6 card types."""
    fc_mod = FlashcardModule()
    res = fc_mod.process(sample_edu_response)

    assert res["module_name"] == "Flashcards"
    assert res["flashcard_count"] > 0
    card_types = {card["type"] for card in res["flashcards"]}
    assert "definition" in card_types
    assert "concept" in card_types
    assert "true_false" in card_types
    assert "fill_in_the_blank" in card_types
    assert "image_placeholder" in card_types
    assert "reverse_card" in card_types


def test_advanced_quiz_engine(sample_edu_response):
    """Verify advanced quiz generator produces 5 question formats with explanations."""
    qz_mod = QuizGeneratorModule()
    res = qz_mod.process(sample_edu_response)

    assert res["total_questions"] >= 5
    q_types = {q["type"] for q in res["quiz_questions"]}
    assert "mcq" in q_types
    assert "true_false" in q_types
    assert "multiple_select" in q_types
    assert "short_answer" in q_types
    assert "scenario" in q_types


def test_mind_map_and_concept_graph(sample_edu_response):
    """Verify mind map tree and concept graph generation."""
    mm_mod = MindMapModule()
    mm_res = mm_mod.process(sample_edu_response)
    assert "children" in mm_res["mind_map_tree"]

    cg_mod = ConceptGraphModule()
    cg_res = cg_mod.process(sample_edu_response)
    assert cg_res["node_count"] >= 3
    assert cg_res["edge_count"] >= 2


def test_revision_assistant(sample_edu_response):
    """Verify revision assistant sheet outputs."""
    rev_mod = RevisionAssistantModule()
    res = rev_mod.process(sample_edu_response)

    assert "ONE-PAGE REVISION SHEET" in res["one_page_revision"]
    assert "EXAM CHEAT SHEET" in res["cheat_sheet"]
    assert len(res["last_minute_revision"]) > 0


def test_interview_prep_module(sample_edu_response):
    """Verify interview preparation questions and rubric generation."""
    iv_mod = InterviewPrepModule()
    res = iv_mod.process(sample_edu_response)

    assert len(res["common_questions"]) >= 1
    assert len(res["advanced_questions"]) >= 1
    assert "Strong Answer (5/5)" in res["evaluation_rubric"]


def test_coding_practice_module(sample_edu_response):
    """Verify coding practice exercise and complexity analysis."""
    cd_mod = CodingPracticeModule()
    res = cd_mod.process(sample_edu_response)

    assert res["challenges_count"] >= 1
    ch = res["coding_challenges"][0]
    assert "O(N)" in ch["time_complexity"]
    assert "sample_solution" in ch


def test_research_assistant_module(sample_edu_response):
    """Verify research assistant gaps, future work, and comparison table."""
    rs_mod = ResearchAssistantModule()
    res = rs_mod.process(sample_edu_response)

    assert len(res["research_gaps"]) >= 1
    assert len(res["future_work"]) >= 1
    assert len(res["comparison_table"]) >= 1


def test_execute_all_via_module_manager(sample_edu_response):
    """Verify execute_all executes all registered modules in singleton module_manager."""
    outs = module_manager.execute_all(sample_edu_response)

    assert "flashcards" in outs
    assert "quizgenerator" in outs
    assert "mindmap" in outs
    assert "conceptgraph" in outs
    assert "revisionassistant" in outs
    assert "interviewprep" in outs
    assert "codingpractice" in outs
    assert "researchassistant" in outs


def test_module_telemetry():
    """Verify recording module telemetry in ConversationMemory."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        db_path = os.path.join(tmp_dir, "test_telemetry.db")
        mem = ConversationMemory(db_path=db_path)
        mem.record_module_telemetry(
            query="Test Module Telemetry",
            module_name="QuizGenerator",
            metrics={"quiz_attempts": 3, "avg_quiz_score": 85.5, "module_execution_latency": 12.4},
        )

        with mem._get_conn() as conn:
            row = conn.execute("SELECT * FROM query_analytics WHERE source_mode = 'learning_module'").fetchone()
            assert row is not None
            assert row["educational_mode"] == "QuizGenerator"
            assert row["quiz_attempts"] == 3


def test_langgraph_pipeline_regression():
    """Verify 12-node LangGraph pipeline executes cleanly without regression."""
    graph = create_ekip_planning_graph()
    state = graph.invoke({"question": "Explain Machine Learning Principles"})
    assert isinstance(state, EKIPGraphState)
