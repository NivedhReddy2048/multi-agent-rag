"""Unit and regression tests for EKIP Platform Main Chat Page UI Redesign."""

import pytest
import streamlit as st
from unittest.mock import patch, MagicMock

import ui.shell
import ui.components
import app


def mock_columns_func(spec, **kwargs):
    count = len(spec) if isinstance(spec, list) else int(spec)
    return [MagicMock() for _ in range(count)]


def test_top_nav_and_header_breadcrumb_removal():
    """Test that top nav and header do NOT render breadcrumbs or search/deploy buttons."""
    mock_session_state = {
        "user": {"first_name": "John", "last_name": "Doe", "username": "jdoe", "email": "john@ekip.ai", "role": "Student"},
        "current_page": "chat",
        "show_profile_dropdown": False
    }

    with patch("streamlit.session_state", mock_session_state), \
         patch("streamlit.markdown") as mock_markdown, \
         patch("streamlit.columns", side_effect=mock_columns_func), \
         patch("streamlit.popover") as mock_popover:

        ui.shell.render_top_nav()

        markdown_calls = [c[0][0] for c in mock_markdown.call_args_list if c[0]]
        combined_markdown = "\n".join(markdown_calls)

        # Assert breadcrumb titles are NOT present in markdown output
        assert "🎓 EKIP Platform" not in combined_markdown, "Breadcrumb '🎓 EKIP Platform' must be removed"
        assert "top-nav-breadcrumb" not in combined_markdown, "Breadcrumb element must be removed"


def test_hero_banner_meta_pills_removal():
    """Test that hero banner renders NO meta pills (Docs Indexed, Search, Alerts, Settings, Student)."""
    with patch("streamlit.markdown") as mock_markdown:
        ui.components.render_hero_banner()

        markdown_calls = [c[0][0] for c in mock_markdown.call_args_list if c[0]]
        combined_markdown = "\n".join(markdown_calls)

        # 1. Assert hero meta pills are removed
        forbidden_pills = ["3 Docs Indexed", "🔍 Search", "🔔 Alerts", "⚙️ Settings", "👤 Student", "hero-meta-pill"]
        for pill in forbidden_pills:
            assert pill not in combined_markdown, f"Hero pill '{pill}' must be removed from hero banner"

        # 2. Assert hero content & knowledge pipeline remain
        assert "Educational Knowledge Companion" in combined_markdown
        assert "Ask Question" in combined_markdown
        assert "Multi-Source Retrieval" in combined_markdown
        assert "Verification & Evidence" in combined_markdown
        assert "Grounded Learning" in combined_markdown


def test_quick_starters_returns_correct_prompts():
    """Test that Quick Start action buttons render enterprise cards and return exact prompts."""
    with patch("streamlit.columns", side_effect=mock_columns_func), \
         patch("streamlit.button") as mock_button, \
         patch("streamlit.markdown"):

        # Mock button click on 'qs_explain'
        def button_side_effect(label, **kwargs):
            return kwargs.get("key") == "qs_explain"

        mock_button.side_effect = button_side_effect

        prompt = ui.components.render_quick_starters()
        assert prompt == "Explain the core concepts of Transformer architectures in Machine Learning.", \
            "Quick starter 'qs_explain' must return exact expected prompt"


def test_sidebar_enterprise_navigation_items():
    """Test that sidebar navigation renders modern vertical navigation buttons with active states."""
    mock_session_state = {"nav_page": "💬 Chat", "current_page": "chat"}

    with patch("streamlit.session_state", mock_session_state), \
         patch("streamlit.button") as mock_button, \
         patch("streamlit.markdown"):

        selected_page = ui.shell.render_sidebar_navigation(doc_cnt=5)

        button_calls = mock_button.call_args_list
        keys = [c[1].get("key") for c in button_calls if c[1].get("key")]

        # Verify all 5 enterprise navigation keys are rendered
        expected_keys = [
            "nav_item_💬 Chat",
            "nav_item_🎓 Student Workspace",
            "nav_item_📊 Analytics",
            "nav_item_📚 Documents",
            "nav_item_🩺 LLM Health & Diagnostics",
        ]
        for key in expected_keys:
            assert key in keys, f"Sidebar navigation item key '{key}' must be rendered"

        # Verify dynamic doc count badge is included in Documents button label
        docs_call = next(c for c in button_calls if c[1].get("key") == "nav_item_📚 Documents")
        assert "5" in docs_call[0][0], "Documents navigation button must display dynamic document count badge"
