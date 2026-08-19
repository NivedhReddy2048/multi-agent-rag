"""Unit and regression tests for Chat History UI alignment and timestamp removal."""

import pytest
import streamlit as st
from unittest.mock import patch, MagicMock

import ui.chat_sidebar
from core.chat.database import init_chat_db, create_chat_session


@pytest.fixture
def temp_chat_db(tmp_path):
    db_file = tmp_path / "test_ekip_chats.db"
    init_chat_db(str(db_file))
    return str(db_file)


def mock_columns_func(spec, **kwargs):
    count = len(spec) if isinstance(spec, list) else int(spec)
    return [MagicMock() for _ in range(count)]


def test_chat_history_sidebar_renders_no_timestamps(temp_chat_db):
    """Test that render_chat_history_sidebar renders message counts but ZERO timestamps."""
    user_id = "test_user_ui"
    s1 = create_chat_session(user_id, "New Chat 1", db_path=temp_chat_db)
    s2 = create_chat_session(user_id, "Explain Quantum Physics", db_path=temp_chat_db)

    mock_sessions = [
        {"id": s1, "title": "New Chat 1", "pinned": 0, "message_count": 0, "updated_at": "2026-08-17T12:00:00Z"},
        {"id": s2, "title": "Explain Quantum Physics", "pinned": 1, "message_count": 5, "updated_at": "2026-08-16T10:00:00Z"},
    ]

    mock_session_state = {"active_chat_id": s1, "editing_chat_id": None, "deleting_chat_id": None}

    with patch("streamlit.session_state", mock_session_state), \
         patch("ui.chat_sidebar.get_chat_sessions", return_value=mock_sessions), \
         patch("streamlit.markdown") as mock_markdown, \
         patch("streamlit.columns", side_effect=mock_columns_func), \
         patch("streamlit.button") as mock_button:

        ui.chat_sidebar.render_chat_history_sidebar(user_id)

        # Collect all markdown string calls
        markdown_calls = [c[0][0] for c in mock_markdown.call_args_list if c[0]]
        combined_markdown = "\n".join(markdown_calls)

        # 1. Assert message counts are present
        assert "0 messages" in combined_markdown, "Message count '0 messages' must be rendered"
        assert "5 messages" in combined_markdown, "Message count '5 messages' must be rendered"

        # 2. Assert NO timestamps are present
        forbidden_timestamps = ["11h ago", "12h ago", "2h ago", "Yesterday", "d ago", "m ago", "Just now", "Recently", "• 2026"]
        for forbidden in forbidden_timestamps:
            assert forbidden not in combined_markdown, f"Timestamp '{forbidden}' must NOT be rendered in Chat History"


def test_chat_history_action_buttons_keys_and_container_width():
    """Test that rename, pin, and delete buttons are rendered with use_container_width=True."""
    mock_sessions = [
        {"id": "chat_100", "title": "Test Chat", "pinned": 0, "message_count": 2, "updated_at": "2026-08-17T12:00:00Z"},
    ]

    mock_session_state = {"active_chat_id": "chat_100", "editing_chat_id": None, "deleting_chat_id": None}

    with patch("streamlit.session_state", mock_session_state), \
         patch("ui.chat_sidebar.get_chat_sessions", return_value=mock_sessions), \
         patch("streamlit.columns", side_effect=mock_columns_func), \
         patch("streamlit.button") as mock_button, \
         patch("streamlit.markdown"):

        ui.chat_sidebar.render_chat_history_sidebar("user_test")

        button_calls = mock_button.call_args_list
        
        # Verify Rename button
        rename_call = next((c for c in button_calls if c[1].get("key") == "edit_chat_chat_100"), None)
        assert rename_call is not None, "Rename button must exist with key edit_chat_chat_100"
        assert rename_call[1].get("use_container_width") is True, "Rename button must use container width for tight layout"

        # Verify Pin button
        pin_call = next((c for c in button_calls if c[1].get("key") == "pin_chat_chat_100"), None)
        assert pin_call is not None, "Pin button must exist with key pin_chat_chat_100"
        assert pin_call[1].get("use_container_width") is True, "Pin button must use container width for tight layout"

        # Verify Delete button
        del_call = next((c for c in button_calls if c[1].get("key") == "del_chat_chat_100"), None)
        assert del_call is not None, "Delete button must exist with key del_chat_chat_100"
        assert del_call[1].get("use_container_width") is True, "Delete button must use container width for tight layout"
