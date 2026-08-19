"""Unit tests for Analytics Data Layer (Task 14)."""

import pytest
from core.analytics import (
    get_user_chat_stats,
    get_user_document_stats,
    get_user_activity_trend,
    get_rag_performance_metrics,
)
from core.chat.database import init_chat_db, create_chat_session, save_message


@pytest.fixture
def temp_chat_db(tmp_path):
    db_file = tmp_path / "test_ekip_chats.db"
    init_chat_db(str(db_file))
    return str(db_file)


def test_user_chat_stats(temp_chat_db):
    user_id = "testuser"
    sid = create_chat_session(user_id, "Test Session", db_path=temp_chat_db)
    save_message(sid, "user", "Hello", db_path=temp_chat_db)
    save_message(sid, "assistant", "Hi there", db_path=temp_chat_db)

    stats = get_user_chat_stats(user_id, db_path=temp_chat_db)
    assert stats["total_chats"] == 1
    assert stats["total_messages"] == 2
    assert stats["avg_messages_per_chat"] == 2.0


def test_user_activity_trend(temp_chat_db):
    user_id = "testuser"
    sid = create_chat_session(user_id, "Trend Test", db_path=temp_chat_db)
    save_message(sid, "user", "Message 1", db_path=temp_chat_db)

    trend = get_user_activity_trend(user_id, days=7, db_path=temp_chat_db)
    assert len(trend) == 7
    assert "date" in trend[0]
    assert "messages" in trend[0]


def test_rag_performance_metrics():
    metrics = get_rag_performance_metrics("testuser")
    assert metrics["avg_confidence_score"] > 0
    assert "queries_by_intent" in metrics
    assert len(metrics["top_sources"]) > 0
