"""Objective 1: SQLite Telemetry Initialization & Migration Regression Suite."""

import pytest
import tempfile
import os
import sqlite3
from core.memory import ConversationMemory
from analytics.telemetry import TelemetryTracker


def test_memory_initialization_in_memory():
    """Verify fresh :memory: database initializes schema immediately."""
    mem = ConversationMemory(":memory:")
    with mem._get_conn() as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        assert "query_analytics" in tables
        assert "conversations" in tables
        assert "messages" in tables
        assert "blocked_queries" in tables


def test_memory_initialization_file_based():
    """Verify fresh file-based database initializes schema immediately."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = os.path.join(tmpdir, "test_conv.db")
        mem = ConversationMemory(db_file)
        with mem._get_conn() as conn:
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            assert "query_analytics" in tables
        mem.close()


def test_record_query_metrics_succeeds():
    """Verify TelemetryTracker.record_query_metrics writes to query_analytics without errors."""
    mem = ConversationMemory(":memory:")
    metrics = TelemetryTracker.record_query_metrics(
        memory_instance=mem,
        query="Test telemetry query",
        intent="general_knowledge",
        confidence=90,
        faithfulness=0.95,
        blocked=False,
        latency_ms=150,
        agent_trace=["Planner", "Synthesizer"],
        source_mode="general_knowledge",
        crag_used=False,
        web_results_count=0,
        prompt_tokens=50,
        completion_tokens=100,
    )
    assert metrics["query"] == "Test telemetry query"
    assert mem.get_total_queries() == 1


def test_telemetry_methods_succeed():
    """Verify all individual record_* telemetry methods succeed."""
    mem = ConversationMemory(":memory:")

    # Planner telemetry
    mem.record_planner_telemetry("Test planner query", {
        "intent": "qa",
        "difficulty": "medium",
        "selected_sources": ["general_ai"],
        "retrieval_strategy": "general_knowledge",
        "estimated_latency": "100ms",
        "estimated_cost": "low",
    })

    # Collection telemetry
    mem.record_collection_telemetry("Test collection query", {
        "sources_requested": ["general_ai"],
        "sources_completed": ["general_ai"],
        "sources_failed": [],
        "total_latency_ms": 120.0,
        "provider_latencies": {"general_ai": 120.0},
    })

    # Verification telemetry
    mem.record_verification_telemetry("Test verification query", {
        "overall_confidence": 0.9,
        "overall_agreement": 1.0,
        "conflicts": [],
        "duplicates": [],
        "total_latency_ms": 10.0,
    })

    # Synthesis telemetry
    mem.record_synthesis_telemetry("Test synthesis query", {
        "educational_mode": "detailed_explanation",
        "guided_questions": ["Q1"],
        "learning_path": True,
        "synthesis_metadata": {"composer_latency_ms": 5.0, "synthesis_latency_ms": 50.0},
    })

    # Module telemetry
    mem.record_module_telemetry("Test module query", "flashcards", {
        "flashcards_generated": 5,
        "quiz_attempts": 2,
        "avg_quiz_score": 85.0,
        "revision_usage": 1,
        "interview_practice": 0,
        "coding_exercises": 0,
        "module_execution_latency": 45.0,
    })

    assert mem.get_total_queries() == 5


def test_backward_compatible_migration():
    """Verify migration alters legacy database schema safely without data loss."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = os.path.join(tmpdir, "legacy.db")
        # Create bare legacy table
        conn = sqlite3.connect(db_file)
        conn.execute("CREATE TABLE query_analytics (id INTEGER PRIMARY KEY, query TEXT)")
        conn.execute("INSERT INTO query_analytics (query) VALUES ('legacy_query')")
        conn.commit()
        conn.close()

        # Initialize ConversationMemory on legacy database
        mem = ConversationMemory(db_file)
        assert mem.get_total_queries() == 1
        with mem._get_conn() as conn:
            row = conn.execute("SELECT * FROM query_analytics WHERE query='legacy_query'").fetchone()
            assert row["query"] == "legacy_query"
        mem.close()
