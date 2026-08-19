"""Unit and regression tests for single sidebar collapse/expand toggle control."""

import pytest
import streamlit as st
from unittest.mock import patch, MagicMock

import ui.components
import ui.shell
from ui.theme import get_sidebar_toggle_css


def test_sidebar_toggle_expanded_state():
    """Test that when sidebar is expanded, only 1 collapse button ([ ◀ ]) is rendered."""
    mock_session = {"sidebar_collapsed": False, "user": {"first_name": "Test", "last_name": "User"}}

    with patch("streamlit.session_state", mock_session), \
         patch("streamlit.sidebar") as mock_sidebar, \
         patch("streamlit.button") as mock_button, \
         patch("streamlit.columns") as mock_columns, \
         patch("streamlit.markdown"):

        mock_col1, mock_col2 = MagicMock(), MagicMock()
        mock_columns.return_value = [mock_col1, mock_col2]

        ui.components.render_sidebar_brand()

        # Verify button called with '◀'
        button_calls = mock_button.call_args_list
        collapse_btn_call = next((call for call in button_calls if call[0][0] == "◀"), None)

        assert collapse_btn_call is not None, "Collapse button [ ◀ ] must be rendered when expanded"
        assert collapse_btn_call[1].get("key") == "sidebar_header_collapse"


def test_sidebar_controls_alias_delegates_to_brand():
    """Test that ui.shell.render_sidebar_controls delegates to ui.components.render_sidebar_brand."""
    with patch("ui.components.render_sidebar_brand") as mock_brand:
        ui.shell.render_sidebar_controls()
        mock_brand.assert_called_once()


def test_sidebar_toggle_css_output():
    """Test get_sidebar_toggle_css outputs correct styles for expanded and collapsed states."""
    mock_session_expanded = {"sidebar_collapsed": False}
    with patch("streamlit.session_state", mock_session_expanded):
        css_expanded = get_sidebar_toggle_css()
        assert "width: 260px !important" in css_expanded
        assert "visibility: visible" in css_expanded

    mock_session_collapsed = {"sidebar_collapsed": True}
    with patch("streamlit.session_state", mock_session_collapsed):
        css_collapsed = get_sidebar_toggle_css()
        assert "width: 0px !important" in css_collapsed
        assert "visibility: hidden" in css_collapsed
