"""Unit tests for EKIP Profile Page layout and vertical scrolling regression prevention."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from ui.profile import render_profile_page


def test_render_profile_page_structure_and_scrolling():
    """Verify that render_profile_page injects scoped overflow-y CSS and renders all profile fields."""
    mock_user = {
        "first_name": "Test",
        "last_name": "User",
        "username": "test_user",
        "email": "test@ekip.ai",
        "phone": "+1234567890",
        "role": "Student",
        "created_at": datetime(2026, 1, 15),
    }

    mock_session_state = {"user": mock_user, "current_page": "profile"}

    with patch("streamlit.session_state", mock_session_state), \
         patch("streamlit.markdown") as mock_markdown, \
         patch("streamlit.button") as mock_button, \
         patch("streamlit.columns") as mock_columns:

        # Set up mock column context manager
        mock_col = MagicMock()
        mock_columns.return_value = [mock_col, mock_col, mock_col]
        mock_button.return_value = False

        # Execute profile page render
        render_profile_page()

        # 1. Verify scoped CSS injection for vertical scrolling
        markdown_calls = [call[0][0] for call in mock_markdown.call_args_list]
        css_injected = any("overflow-y: auto" in call for call in markdown_calls)
        assert css_injected, "Profile page must inject scoped overflow-y: auto CSS rule"

        # 2. Verify Profile Card contains all required profile fields without iframe height restriction
        card_html = next((c for c in markdown_calls if '<div style="max-width:480px;' in c), None)
        assert card_html is not None, "Profile card HTML structure must be rendered"
        assert "📛 Username" in card_html
        assert "test_user" in card_html
        assert "📧 Email" in card_html
        assert "test@ekip.ai" in card_html
        assert "📞 Phone" in card_html
        assert "+1234567890" in card_html
        assert "🎓 Role" in card_html
        assert "Student" in card_html
        assert "📅 Joined" in card_html
        assert "Jan 2026" in card_html

        # 3. Verify Back and Logout buttons are rendered
        button_keys = [kwargs.get("key") for call in mock_button.call_args_list for args, kwargs in [call]]
        assert "profile_back" in button_keys, "Profile back button must be rendered"
        assert "profile_logout" in button_keys, "Profile logout button must be rendered"
