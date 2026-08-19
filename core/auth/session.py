"""Session state management helpers for Streamlit auth integration."""

import streamlit as st
from typing import Optional, Dict, Any
from core.auth.database import (
    get_user_by_username,
    get_user_by_email,
    generate_remember_token,
    validate_remember_token,
    invalidate_remember_token,
)


def initialize_auth_state() -> None:
    """Set initial default values in st.session_state for authentication."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "user" not in st.session_state:
        st.session_state["user"] = None
    if "remember_me" not in st.session_state:
        st.session_state["remember_me"] = False
    if "auth_view" not in st.session_state:
        st.session_state["auth_view"] = "cover"
    if "user_email" not in st.session_state:
        st.session_state["user_email"] = None
    if "user_name" not in st.session_state:
        st.session_state["user_name"] = None
    if "sidebar_collapsed" not in st.session_state:
        st.session_state["sidebar_collapsed"] = False
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "chat"
    if "show_profile_dropdown" not in st.session_state:
        st.session_state["show_profile_dropdown"] = False


def login_user(username: str, remember: bool = False) -> bool:
    """Log in user by username/email, set session state, and save remember token if requested."""
    user = get_user_by_username(username) or get_user_by_email(username)
    if not user:
        return False

    st.session_state["authenticated"] = True
    st.session_state["user"] = user
    st.session_state["user_email"] = user.get("email")
    first = user.get("first_name", "")
    last = user.get("last_name", "")
    name = f"{first} {last}".strip()
    st.session_state["user_name"] = name or user.get("username")
    st.session_state["remember_me"] = remember
    st.session_state["auth_view"] = "workspace"
    st.session_state["current_page"] = "chat"

    # Load theme from DB
    from core.auth.database import get_user_theme
    user_theme = get_user_theme(user["username"])
    st.session_state["theme"] = user_theme if user_theme else "dark"

    if remember:
        token = generate_remember_token(user["username"])
        try:
            st.query_params["token"] = token
        except Exception:
            pass

    return True


def logout_user() -> None:
    """Clear session and redirect to cover."""
    user = st.session_state.get("user")
    token = None
    try:
        token = st.query_params.get("token")
    except Exception:
        pass

    if user and isinstance(user, dict) and user.get("username"):
        invalidate_remember_token(user["username"])
    elif token:
        invalidate_remember_token(token)

    try:
        st.query_params.clear()
    except Exception:
        pass

    keys_to_clear = [
        "authenticated", "user", "theme", "current_page",
        "active_chat_id", "messages", "chat_title",
        "sidebar_collapsed", "show_profile_dropdown",
        "auth_view", "signup_success", "login_show_password",
        "user_email", "user_name", "remember_me"
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    st.session_state.authenticated = False
    st.session_state.auth_view = "cover"
    st.session_state.theme = "dark"


def check_remember_me() -> None:
    """Check query params for remember token on app load and perform silent auto-login."""
    if st.session_state.get("authenticated", False):
        return

    token = None
    try:
        token = st.query_params.get("token")
    except Exception:
        pass

    if token:
        username = validate_remember_token(token)
        if username:
            login_user(username, remember=True)
        else:
            try:
                st.query_params.clear()
            except Exception:
                pass
