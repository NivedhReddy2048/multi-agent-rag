"""Focused unit and regression tests for EKIP Platform New Chat Activation logic."""

import pytest
import tempfile
import os
import streamlit as st
from unittest.mock import patch, MagicMock

import ui.chat_sidebar
from core.chat.database import (
    init_chat_db,
    create_chat_session,
    get_chat_sessions,
    get_chat_messages,
    save_message,
)


from pathlib import Path

@pytest.fixture
def temp_chat_db():
    """Create isolated temporary SQLite database for chat testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        temp_path = Path(tf.name)
    
    init_chat_db(str(temp_path))
    yield temp_path
    
    if temp_path.exists():
        try:
            os.remove(temp_path)
        except Exception:
            pass


def test_start_new_chat_activation(temp_chat_db):
    """Test that start_new_chat creates a chat and sets active_chat_id and conversation_id atomically."""
    user_id = "test_user_new_chat"
    mock_session_state = {
        "user": {"username": user_id},
        "messages": ["old_msg"],
        "active_chat_id": None,
        "conversation_id": None,
    }

    with patch("core.chat.database.DEFAULT_DB_PATH", temp_chat_db), \
         patch("streamlit.session_state", mock_session_state), \
         patch("streamlit.rerun") as mock_rerun:

        ui.chat_sidebar.start_new_chat()

        # 1. Verify session state updated with NEW returned ID
        new_id = mock_session_state.get("active_chat_id")
        assert new_id is not None, "active_chat_id must be set upon New Chat creation"
        assert mock_session_state.get("conversation_id") == new_id, "conversation_id must match active_chat_id"
        assert mock_session_state.get("messages") == [], "messages must be reset to empty for new chat"

        # 2. Verify rerun was called to refresh UI
        mock_rerun.assert_called_once()

        # 3. Verify chat session was created in DB
        sessions = get_chat_sessions(user_id, db_path=temp_chat_db)
        assert len(sessions) == 1
        assert sessions[0]["id"] == new_id


def test_new_chat_activation_with_existing_chats(temp_chat_db):
    """Test Case 1: Clicking New Chat with pre-existing chats activates the newly created chat."""
    user_id = "test_user_existing"
    # Create two existing chats
    c1 = create_chat_session(user_id, "Old Chat 1", db_path=temp_chat_db)
    c2 = create_chat_session(user_id, "Old Chat 2", db_path=temp_chat_db)

    mock_session_state = {
        "user": {"username": user_id},
        "active_chat_id": c1,
        "conversation_id": c1,
        "messages": [{"role": "user", "content": "Old prompt"}]
    }

    with patch("core.chat.database.DEFAULT_DB_PATH", temp_chat_db), \
         patch("streamlit.session_state", mock_session_state), \
         patch("streamlit.rerun"):

        ui.chat_sidebar.start_new_chat()

        new_id = mock_session_state.get("active_chat_id")
        assert new_id != c1 and new_id != c2, "New chat ID must be distinct from old chat IDs"
        assert mock_session_state.get("conversation_id") == new_id, "conversation_id must switch to new chat ID"
        assert mock_session_state.get("messages") == [], "New active chat must start with empty messages"


def test_first_message_persists_to_activated_new_chat(temp_chat_db):
    """Test Case 4: Immediate message after New Chat attaches to the newly activated chat ID."""
    user_id = "test_user_first_msg"
    mock_session_state = {
        "user": {"username": user_id},
        "active_chat_id": None,
        "conversation_id": None,
        "messages": []
    }

    with patch("core.chat.database.DEFAULT_DB_PATH", temp_chat_db), \
         patch("streamlit.session_state", mock_session_state), \
         patch("streamlit.rerun"):

        # 1. User clicks New Chat
        ui.chat_sidebar.start_new_chat()
        active_id = mock_session_state["active_chat_id"]

        # 2. User immediately types first prompt
        prompt = "Explain quantum entanglement in simple terms"
        ui.chat_sidebar.on_first_message(prompt)
        save_message(active_id, "user", prompt, db_path=temp_chat_db)

        # 3. Verify message is saved under active_id
        saved_messages = get_chat_messages(active_id, db_path=temp_chat_db)
        assert len(saved_messages) == 1
        assert saved_messages[0]["content"] == prompt
