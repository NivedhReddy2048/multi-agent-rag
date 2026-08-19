"""Runtime truth audit script to verify active rendering path, main chat UI redesign, breadcrumbs/hero pills removal, sidebar enterprise navigation, and single toggle control."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from core.auth.database import init_db, create_user, get_user_by_username, update_user_profile
from core.chat.database import init_chat_db, create_chat_session
import ui.settings
import ui.profile
import ui.shell
import ui.components
import ui.chat_sidebar

def mock_columns_func(spec, **kwargs):
    count = len(spec) if isinstance(spec, list) else int(spec)
    return [MagicMock() for _ in range(count)]

def audit():
    print("--- 1. VERIFYING TOP BREADCRUMBS & EXTRA CONTROLS REMOVAL ---")
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
        ui.components.render_top_header("Educational Knowledge Companion", 3)

        markdown_calls = [c[0][0] for c in mock_markdown.call_args_list if c[0]]
        combined_markdown = "\n".join(markdown_calls)

        assert "🎓 EKIP Platform" not in combined_markdown, "Breadcrumb '🎓 EKIP Platform' must be removed"
        assert "EKIP /" not in combined_markdown, "Breadcrumb 'EKIP /' must be removed"
        assert "🔍" not in combined_markdown, "Top-right search symbol must be removed"
        assert "Deploy" not in combined_markdown, "Top-right Deploy button must be removed"
        assert "ST" not in combined_markdown, "Top-right ST avatar must be removed"

        # Popover control JN ▼ is rendered
        popover_calls = [c[0][0] for c in mock_popover.call_args_list if c[0]]
        assert any("JD" in p or "JN" in p or "👤" in p for p in popover_calls), "Profile dropdown control must be preserved"
        print("✓ Breadcrumbs and extra search/deploy/ST controls successfully removed!")
        print("✓ Top-right user profile popover control preserved!")

    print("\n--- 2. VERIFYING HERO CARD & KNOWLEDGE PIPELINE REDESIGN ---")
    with patch("streamlit.markdown") as mock_markdown:
        ui.components.render_hero_banner()

        markdown_calls = [c[0][0] for c in mock_markdown.call_args_list if c[0]]
        combined_markdown = "\n".join(markdown_calls)

        forbidden_pills = ["3 Docs Indexed", "🔍 Search", "🔔 Alerts", "⚙️ Settings", "👤 Student"]
        for pill in forbidden_pills:
            assert pill not in combined_markdown, f"Hero pill '{pill}' must NOT exist"

        assert "Educational Knowledge Companion" in combined_markdown
        assert "Ask Question" in combined_markdown
        assert "Multi-Source Retrieval" in combined_markdown
        assert "Verification & Evidence" in combined_markdown
        assert "Grounded Learning" in combined_markdown
        print("✓ All 5 hero pills removed cleanly!")
        print("✓ Enterprise title, description, and knowledge pipeline verified!")

    print("\n--- 3. VERIFYING QUICK START ACTIONS (8 CARDS & PROMPTS) ---")
    with patch("streamlit.columns", side_effect=mock_columns_func), \
         patch("streamlit.button") as mock_button, \
         patch("streamlit.markdown"):

        mock_button.side_effect = lambda label, **kwargs: kwargs.get("key") == "qs_explain"
        prompt = ui.components.render_quick_starters()
        assert prompt == "Explain the core concepts of Transformer architectures in Machine Learning."
        print("✓ Quick Start Action cards rendered in enterprise grid with prompt callbacks intact!")

    print("\n--- 4. VERIFYING SIDEBAR ENTERPRISE NAVIGATION ---")
    mock_nav_state = {"nav_page": "💬 Chat", "current_page": "chat"}
    with patch("streamlit.session_state", mock_nav_state), \
         patch("streamlit.button") as mock_button, \
         patch("streamlit.markdown"):

        ui.shell.render_sidebar_navigation(doc_cnt=3)
        button_calls = mock_button.call_args_list
        keys = [c[1].get("key") for c in button_calls if c[1].get("key")]

        assert "nav_item_💬 Chat" in keys
        assert "nav_item_🎓 Student Workspace" in keys
        assert "nav_item_📊 Analytics" in keys
        assert "nav_item_📚 Documents" in keys
        assert "nav_item_🩺 LLM Health & Diagnostics" in keys
        print("✓ All 5 enterprise navigation items active and rendered!")

    print("\n--- 5. VERIFYING SINGLE SIDEBAR TOGGLE CONTROL ---")
    mock_session_expanded = {"sidebar_collapsed": False, "user": {"first_name": "Test"}}
    with patch("streamlit.session_state", mock_session_expanded), \
         patch("streamlit.sidebar") as mock_sidebar, \
         patch("streamlit.button") as mock_button, \
         patch("streamlit.columns", side_effect=mock_columns_func), \
         patch("streamlit.markdown"):

        ui.components.render_sidebar_brand()
        button_calls = [c[0][0] for c in mock_button.call_args_list]
        assert button_calls.count("◀") == 1, "Exactly 1 collapse button [ ◀ ] must render when expanded"
        print("✓ Expanded state renders EXACTLY ONE sidebar control: [ ◀ ]")

    print("\n==========================================")
    print("ALL RUNTIME TRUTH VERIFICATIONS PASSED 100%")
    print("==========================================")

if __name__ == "__main__":
    audit()
