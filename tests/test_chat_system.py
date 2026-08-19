"""Unit tests for EKIP Chat System (Task 10–12)."""

import pytest
import os
from pathlib import Path
from core.chat.database import (
    init_chat_db,
    create_chat_session,
    get_chat_sessions,
    get_chat_session,
    update_chat_title,
    toggle_pin_chat,
    delete_chat_session,
    increment_message_count,
    update_chat_preview,
    save_message,
    get_chat_messages,
    get_message_count,
    delete_chat_messages,
)
from core.chat.naming import generate_chat_title


@pytest.fixture
def temp_chat_db(tmp_path):
    db_file = tmp_path / "test_ekip_chats.db"
    init_chat_db(str(db_file))
    return str(db_file)


def test_naming_generator():
    title1 = generate_chat_title("Explain the theory of relativity in simple terms?")
    assert "Explain the theory of relativity" in title1
    assert len(title1) <= 40

    title2 = generate_chat_title("Summarize my uploaded Deep_Solar_System_Report.pdf")
    assert "Summarize Deep Solar System Report" in title2

    assert generate_chat_title("Hi") == "Hi"
    assert generate_chat_title("") == "New Chat"


def test_chat_db_lifecycle(temp_chat_db):
    user_id = "testuser"
    
    # Create
    sid = create_chat_session(user_id, "New Chat", "First query", db_path=temp_chat_db)
    assert sid is not None
    
    # Retrieve
    sess = get_chat_session(sid, temp_chat_db)
    assert sess["user_id"] == user_id
    assert sess["title"] == "New Chat"

    # Update Title
    assert update_chat_title(sid, "Theory of Relativity", temp_chat_db) is True
    assert get_chat_session(sid, temp_chat_db)["title"] == "Theory of Relativity"

    # Pin
    assert toggle_pin_chat(sid, temp_chat_db) is True
    assert get_chat_session(sid, temp_chat_db)["pinned"] == 1

    # Increment Message Count
    assert increment_message_count(sid, temp_chat_db) is True
    assert get_chat_session(sid, temp_chat_db)["message_count"] == 1

    # List Sessions
    sessions = get_chat_sessions(user_id, temp_chat_db)
    assert len(sessions) == 1
    assert sessions[0]["id"] == sid

    # Delete
    assert delete_chat_session(sid, temp_chat_db) is True
    assert get_chat_session(sid, temp_chat_db) is None


def test_message_persistence(temp_chat_db):
    user_id = "testuser"
    sid = create_chat_session(user_id, "Persistence Test", db_path=temp_chat_db)

    # Save messages
    assert save_message(sid, "user", "What is quantum computing?", db_path=temp_chat_db) is True
    assert save_message(sid, "assistant", "Quantum computing uses qubits...", db_path=temp_chat_db) is True

    # Retrieve messages
    msgs = get_chat_messages(sid, db_path=temp_chat_db)
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "What is quantum computing?"
    assert msgs[1]["role"] == "assistant"

    # Message count
    assert get_message_count(sid, db_path=temp_chat_db) == 2

    # Delete messages
    assert delete_chat_messages(sid, db_path=temp_chat_db) is True
    assert get_message_count(sid, db_path=temp_chat_db) == 0
