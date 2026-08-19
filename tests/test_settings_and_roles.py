"""Unit and regression tests for EKIP Settings page role editing, persistence, and Info tab rendering."""

import os
import tempfile
import importlib
import pytest
from unittest.mock import MagicMock, patch

from core.auth.database import (
    init_db,
    create_user,
    get_user_by_username,
    update_user_profile,
)
from core.auth.validators import validate_role


@pytest.fixture
def temp_db():
    """Create temporary SQLite database for testing role updates."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        temp_path = tf.name
    init_db(temp_path)
    yield temp_path
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except Exception:
            pass


def test_role_validation():
    """Test role validator enforcing exact supported roles ('Student', 'Researcher')."""
    assert validate_role("Student") is True
    assert validate_role("Researcher") is True

    with pytest.raises(ValueError, match="Role must be exactly 'Student' or 'Researcher'"):
        validate_role("Admin")

    with pytest.raises(ValueError):
        validate_role("InvalidRole")


def test_role_persistence_in_database(temp_db):
    """Test updating user role in SQLite database via update_user_profile and checking persistence."""
    user = create_user(
        first_name="Role",
        last_name="Tester",
        username="roletester",
        email="role@ekip.ai",
        phone="12345678901",
        role="Student",
        password="Password123",
        db_path=temp_db,
    )
    assert user["role"] == "Student"

    # 1. Update role: Student -> Researcher
    updated_user = update_user_profile(
        username="roletester",
        first_name="Role",
        last_name="Tester",
        phone="12345678901",
        role="Researcher",
        db_path=temp_db,
    )
    assert updated_user["role"] == "Researcher"

    # Verify persistent retrieval from DB
    fetched = get_user_by_username("roletester", db_path=temp_db)
    assert fetched["role"] == "Researcher"

    # 2. Update role back: Researcher -> Student
    updated_user_back = update_user_profile(
        username="roletester",
        first_name="Role",
        last_name="Tester",
        phone="12345678901",
        role="Student",
        db_path=temp_db,
    )
    assert updated_user_back["role"] == "Student"
    assert get_user_by_username("roletester", db_path=temp_db)["role"] == "Student"


def test_invalid_role_rejected_by_update_user_profile(temp_db):
    """Test that attempting to persist an invalid role raises ValueError."""
    create_user(
        first_name="Role",
        last_name="Reject",
        username="rolereject",
        email="reject@ekip.ai",
        phone=None,
        role="Student",
        password="Password123",
        db_path=temp_db,
    )

    with pytest.raises(ValueError):
        update_user_profile(
            username="rolereject",
            first_name="Role",
            last_name="Reject",
            role="SuperAdmin",
            db_path=temp_db,
        )


def test_render_settings_page_tabs_and_info():
    """Test active render_settings_page module execution, verifying 3 tabs, enabled selectbox, and Info content."""
    import ui.settings
    importlib.reload(ui.settings)

    mock_user = {
        "first_name": "Alex",
        "last_name": "Smith",
        "username": "alexsmith",
        "email": "alex@ekip.ai",
        "phone": "12345678901",
        "role": "Student",
        "theme": "dark",
    }

    mock_session = {"user": mock_user, "current_page": "settings"}

    with patch("streamlit.session_state", mock_session), \
         patch("ui.settings.get_user_by_username", return_value=mock_user), \
         patch("streamlit.tabs") as mock_tabs, \
         patch("streamlit.markdown") as mock_markdown, \
         patch("streamlit.selectbox") as mock_selectbox:

        mock_tab1, mock_tab2, mock_tab3 = MagicMock(), MagicMock(), MagicMock()
        mock_tabs.return_value = [mock_tab1, mock_tab2, mock_tab3]

        ui.settings.render_settings_page()

        # 1. Verify 3 tabs created
        mock_tabs.assert_called_once_with(["👤 Profile", "🎨 Appearance", "ℹ️ Info"])

        # 2. Verify Role selectbox rendered with options and NOT disabled
        selectbox_calls = mock_selectbox.call_args_list
        role_call = next((call for call in selectbox_calls if call[0][0] == "Role"), None)
        assert role_call is not None, "Role selectbox must be rendered in Profile tab"
        
        # Verify disabled parameter is not True
        kwargs = role_call[1]
        assert kwargs.get("disabled") is not True, "Role selectbox must NOT be disabled"
        assert kwargs.get("options") == ["Student", "Researcher"], "Role options must be ['Student', 'Researcher']"

        # 3. Verify markdown content includes Info section details
        markdown_calls = [call[0][0] for call in mock_markdown.call_args_list]
        info_rendered = any("About EKIP" in call for call in markdown_calls)
        assert info_rendered, "Info tab content must be rendered"


def test_profile_page_displays_updated_role(temp_db):
    """Test that updating role in Settings persists and is rendered on Profile page."""
    import ui.profile
    importlib.reload(ui.profile)

    user = create_user(
        first_name="Jane",
        last_name="Doe",
        username="janedoe",
        email="jane@ekip.ai",
        phone="98765432101",
        role="Student",
        password="Password123",
        db_path=temp_db,
    )
    assert user["role"] == "Student"

    # Update role in DB
    updated = update_user_profile(
        username="janedoe",
        first_name="Jane",
        last_name="Doe",
        role="Researcher",
        db_path=temp_db,
    )

    mock_session = {"user": updated, "current_page": "profile"}

    with patch("streamlit.session_state", mock_session), \
         patch("streamlit.markdown") as mock_markdown:

        ui.profile.render_profile_page()

        markdown_calls = [call[0][0] for call in mock_markdown.call_args_list]
        combined_markdown = "\n".join(markdown_calls)

        assert "Researcher" in combined_markdown, "Profile page must render updated 'Researcher' role"
