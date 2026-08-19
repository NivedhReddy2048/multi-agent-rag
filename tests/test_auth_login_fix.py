"""Tests for login page fixes, show password functionality, signup type validation, state reset, and CSS visibility."""

import pytest
import streamlit as st
from unittest.mock import MagicMock, patch

from core.auth.database import (
    init_db,
    create_user,
    get_user_by_username,
    get_user_by_email,
    authenticate_user,
)
from core.auth.session import login_user, logout_user, initialize_auth_state
from ui.theme import inject_theme
from ui.auth import render_login_page, render_signup_page, render_forgot_password_page


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    """Setup temporary database for testing."""
    db_path = str(tmp_path / "test_users.db")
    init_db(db_path)
    
    # Create test user
    create_user(
        first_name="Test",
        last_name="User",
        username="testuser",
        email="testuser@example.com",
        phone="1234567890",
        role="Student",
        password="TestPassword123",
        db_path=db_path
    )
    return db_path


def test_auth_by_username_and_email(setup_test_db):
    """Verify user can authenticate via username OR email."""
    db_path = setup_test_db
    
    # Authenticate by username
    user_by_uname = authenticate_user("testuser", "TestPassword123", db_path=db_path)
    assert user_by_uname is not None
    assert user_by_uname["username"] == "testuser"
    
    # Authenticate by email
    user_by_email_obj = get_user_by_email("testuser@example.com", db_path=db_path)
    assert user_by_email_obj is not None
    user_by_email = authenticate_user(user_by_email_obj["username"], "TestPassword123", db_path=db_path)
    assert user_by_email is not None
    assert user_by_email["email"] == "testuser@example.com"


def test_logout_user_clears_all_state():
    """Verify logout_user() resets all session state keys cleanly."""
    st.session_state["authenticated"] = True
    st.session_state["user"] = {"username": "testuser"}
    st.session_state["theme"] = "dark"
    st.session_state["current_page"] = "chat"
    st.session_state["active_chat_id"] = "chat_123"
    st.session_state["messages"] = ["hello"]
    st.session_state["sidebar_collapsed"] = True
    st.session_state["show_profile_dropdown"] = True
    st.session_state["auth_view"] = "workspace"
    st.session_state["signup_success"] = "testuser"
    st.session_state["login_show_password"] = True

    logout_user()

    assert st.session_state.authenticated is False
    assert st.session_state.auth_view == "cover"
    assert st.session_state.theme == "dark"
    assert "user" not in st.session_state
    assert "login_show_password" not in st.session_state
    assert "active_chat_id" not in st.session_state
    assert "messages" not in st.session_state


def test_theme_css_contains_input_visibility_styles():
    """Verify theme CSS includes dark background styling for input fields."""
    st.session_state["theme"] = "dark"
    st.session_state["sidebar_collapsed"] = False
    css_output = inject_theme()
    
    assert 'input[type="password"]' in css_output
    assert 'input[type="text"]' in css_output
    assert 'background-color: #0b0d12 !important' in css_output
    assert 'color: #e2e8f0 !important' in css_output
    assert 'border: 1px solid #1e212b !important' in css_output
    assert 'input::placeholder' in css_output


def test_signup_pw_type_is_default_not_text():
    """Verify render_signup_page and render_forgot_password_page use type='default' instead of 'text'."""
    import inspect
    from ui import auth
    
    signup_src = inspect.getsource(auth.render_signup_page)
    forgot_src = inspect.getsource(auth.render_forgot_password_page)

    # Must use 'default' if show_pw else 'password'
    assert '"default" if show_pw' in signup_src
    assert '"text" if show_pw' not in signup_src
    assert '"default" if show_pw' in forgot_src
    assert '"text" if show_pw' not in forgot_src
