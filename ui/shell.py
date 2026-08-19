"""Top Navigation Shell component for authenticated EKIP workspace."""

import streamlit as st
from typing import Dict, Any, Optional
from core.auth.session import logout_user


def get_user_initials(user: Optional[Dict[str, Any]]) -> str:
    """Extract 1-2 character uppercase initials from user dictionary."""
    if not user:
        return "EK"
    fn = user.get("first_name", "").strip()
    ln = user.get("last_name", "").strip()
    un = user.get("username", "").strip()
    
    if fn and ln:
        return f"{fn[0]}{ln[0]}".upper()
    elif fn:
        return fn[:2].upper()
    elif un:
        return un[:2].upper()
    return "US"


def get_avatar_html(user: Optional[Dict[str, Any]], size: str = "small") -> str:
    """Generate HTML snippet for user avatar (profile image or initials circle).
    
    size: 'small' (32px), 'medium' (48px), 'large' (80px)
    """
    size_map = {"small": 32, "medium": 52, "large": 84}
    font_map = {"small": 12, "medium": 18, "large": 28}
    px = size_map.get(size, 32)
    fs = font_map.get(size, 12)

    img_b64 = user.get("profile_image_b64") if user else None
    if img_b64:
        return (
            f'<img src="data:image/png;base64,{img_b64}" '
            f'style="width: {px}px; height: {px}px; border-radius: 50%; '
            f'object-fit: cover; border: 2px solid rgba(239, 68, 68, 0.5); '
            f'box-shadow: 0 2px 8px rgba(0,0,0,0.3);" />'
        )

    initials = get_user_initials(user)
    return (
        f'<div style="width: {px}px; height: {px}px; border-radius: 50%; '
        f'background: linear-gradient(135deg, #ef4444 0%, #8b5cf6 100%); '
        f'color: #ffffff; font-size: {fs}px; font-weight: 700; '
        f'display: flex; align-items: center; justify-content: center; '
        f'text-transform: uppercase; letter-spacing: 0.05em; '
        f'box-shadow: 0 2px 8px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2);">'
        f'{initials}</div>'
    )


def render_sidebar_controls():
    """Alias delegating to render_sidebar_brand for unified brand header and single collapse button."""
    from ui.components import render_sidebar_brand
    render_sidebar_brand()


def render_top_nav():
    """Renders top-right user profile popover card without top breadcrumb bars or extra search/deploy buttons."""
    user = st.session_state.get("user", {}) or {}
    
    st.markdown(
        """
        <style>
        .role-pill {
            font-size: 11px;
            font-weight: 600;
            background: var(--border);
            color: var(--input-focus);
            padding: 2px 10px;
            border-radius: 12px;
            display: inline-block;
            margin-top: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, col_nav_right = st.columns([8, 2])

    with col_nav_right:
        initials = get_user_initials(user)
        with st.popover(f"👤 {initials} ▼", use_container_width=True, help="User Profile"):
            full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user.get("username", "User")
            email = user.get("email", "")
            role = user.get("role", "Student")
            avatar_html = get_avatar_html(user, "medium")

            st.markdown(
                f"""
                <div style="text-align: center; padding: 8px 0 12px 0;">
                    <div style="display: flex; justify-content: center; margin-bottom: 8px;">
                        {avatar_html}
                    </div>
                    <div style="color: var(--text-primary); font-weight: 600; font-size: 1rem;">{full_name}</div>
                    <div style="color: var(--text-secondary); font-size: 0.8rem; margin-bottom: 4px;">{email}</div>
                    <span class="role-pill">{role}</span>
                </div>
                <hr style="border: 0; border-top: 1px solid var(--border); margin: 10px 0;" />
                """,
                unsafe_allow_html=True,
            )

            if st.button("👤 View Profile", key="dd_view_profile", use_container_width=True):
                st.session_state["current_page"] = "profile"
                st.session_state["show_profile_dropdown"] = False
                st.rerun()

            if st.button("⚙️ Settings", key="dd_settings", use_container_width=True):
                st.session_state["current_page"] = "settings"
                st.session_state["show_profile_dropdown"] = False
                st.rerun()

            st.markdown('<hr style="border: 0; border-top: 1px solid #1e212b; margin: 10px 0;" />', unsafe_allow_html=True)

            if st.button("🚪 Logout", key="dd_logout", type="primary", use_container_width=True):
                logout_user()
                st.session_state["auth_view"] = "cover"
                st.session_state["current_page"] = "chat"
                st.session_state["show_profile_dropdown"] = False
                st.rerun()


def render_sidebar_navigation(doc_cnt: int = 3) -> str:
    """Renders modern enterprise vertical navigation menu in sidebar."""
    st.markdown(
        """
        <div style="font-size: 11px; font-weight: 700; color: var(--text-secondary); letter-spacing: 0.05em; margin-bottom: 8px; margin-top: 4px;">
            NAVIGATION
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = "💬 Chat"

    active_page = st.session_state["nav_page"]

    nav_items = [
        ("💬 Chat", "🔴  Chat"),
        ("🎓 Student Workspace", "🎓  Student Workspace"),
        ("📊 Analytics", "📊  Analytics"),
        ("📚 Documents", f"📁  Documents          {doc_cnt}"),
        ("🩺 LLM Health & Diagnostics", "🩺  LLM Health & Diagnostics"),
    ]

    selected_page = active_page

    for target_page, label in nav_items:
        is_active = (active_page == target_page)
        btn_key = f"nav_item_{target_page}"
        btn_type = "primary" if is_active else "secondary"

        if st.button(label, key=btn_key, use_container_width=True, type=btn_type):
            st.session_state["nav_page"] = target_page
            st.session_state["current_page"] = "chat" if target_page == "💬 Chat" else target_page
            selected_page = target_page
            st.rerun()

    return selected_page
