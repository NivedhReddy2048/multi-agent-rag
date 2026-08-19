"""Unit tests for User Preferences & Workspace State (Task 13)."""

import pytest
from core.auth.database import (
    init_db,
    init_user_preferences,
    get_user_preferences,
    update_user_preferences,
)


@pytest.fixture
def temp_user_db(tmp_path):
    db_file = tmp_path / "test_ekip_users.db"
    init_db(str(db_file))
    return str(db_file)


def test_user_preferences_default(temp_user_db):
    prefs = get_user_preferences("testuser", temp_user_db)
    assert prefs["user_id"] == "testuser"
    assert prefs["show_welcome_card"] == 1
    assert prefs["default_view"] == "dashboard"


def test_user_preferences_update(temp_user_db):
    user_id = "testuser"

    # Update show_welcome_card
    assert update_user_preferences(user_id, temp_user_db, show_welcome_card=0) is True
    prefs = get_user_preferences(user_id, temp_user_db)
    assert prefs["show_welcome_card"] == 0

    # Update default_view & sidebar_collapsed
    assert update_user_preferences(user_id, temp_user_db, default_view="chat", sidebar_collapsed=1) is True
    prefs2 = get_user_preferences(user_id, temp_user_db)
    assert prefs2["default_view"] == "chat"
    assert prefs2["sidebar_collapsed"] == 1
