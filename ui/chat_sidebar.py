"""Chat history sidebar component for EKIP Platform."""

import streamlit as st
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from core.chat.database import (
    get_chat_sessions,
    create_chat_session,
    update_chat_title,
    toggle_pin_chat,
    delete_chat_session,
    update_chat_preview,
)
from core.chat.naming import generate_chat_title


def format_relative_time(dt_val) -> str:
    """Convert datetime to 'Just now', '2m ago', '1h ago', 'Yesterday', 'Aug 16'"""
    if not dt_val:
        return "Recently"

    if isinstance(dt_val, str):
        try:
            dt = datetime.fromisoformat(dt_val.replace("Z", "+00:00"))
        except Exception:
            return "Recently"
    elif isinstance(dt_val, datetime):
        dt = dt_val
    else:
        return "Recently"

    now = datetime.now()
    diff = now - dt.replace(tzinfo=None)
    seconds = diff.total_seconds()

    if seconds < 60:
        return "Just now"
    if seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    if diff.days == 1:
        return "Yesterday"
    if diff.days < 7:
        return f"{diff.days}d ago"
    return dt.strftime("%b %d")


def start_new_chat():
    """Create a new chat session and make it active."""
    user = st.session_state.get("user", {}) or {}
    user_id = user.get("username", "guest")
    session_id = create_chat_session(user_id, "New Chat")
    st.session_state["active_chat_id"] = session_id
    st.session_state["conversation_id"] = session_id
    st.session_state["chat_title"] = "New Chat"
    st.session_state["messages"] = []
    st.session_state["current_page"] = "chat"
    st.session_state["nav_page"] = "💬 Chat"
    st.rerun()


def on_first_message(user_message: str):
    """Auto-generate chat title and save preview on first user message."""
    active_id = st.session_state.get("active_chat_id") or st.session_state.get("conversation_id")
    user = st.session_state.get("user", {}) or {}
    user_id = user.get("username", "guest")

    if not active_id:
        active_id = create_chat_session(user_id, "New Chat", user_message)
        st.session_state["active_chat_id"] = active_id
        st.session_state["conversation_id"] = active_id

    title = generate_chat_title(user_message)
    update_chat_title(active_id, title)
    update_chat_preview(active_id, user_message[:100])
    st.session_state["chat_title"] = title


def load_chat_session(session_id: str):
    """Load chat session metadata and message history into session state."""
    from core.chat.database import get_chat_session, get_chat_messages

    session = get_chat_session(session_id)
    if not session:
        return
    messages = get_chat_messages(session_id)
    st.session_state["active_chat_id"] = session_id
    st.session_state["conversation_id"] = session_id
    st.session_state["chat_title"] = session.get("title", "New Chat")
    st.session_state["messages"] = messages
    st.session_state["current_page"] = "chat"
    st.session_state["nav_page"] = "💬 Chat"
    st.rerun()


def render_chat_history_sidebar(user_id: str):
    """Renders the complete interactive chat history list in the sidebar."""
    if "editing_chat_id" not in st.session_state:
        st.session_state["editing_chat_id"] = None
    if "deleting_chat_id" not in st.session_state:
        st.session_state["deleting_chat_id"] = None

    # New Chat Primary Button
    if st.button("➕ New Chat", key="btn_sidebar_new_chat", use_container_width=True, type="primary"):
        start_new_chat()

    st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)

    sessions = get_chat_sessions(user_id)
    chat_count = len(sessions)

    # Header with Count Badge
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <span style="font-size: 11px; font-weight: 700; color: var(--text-secondary); letter-spacing: 0.05em;">CHAT HISTORY</span>
            <span style="background: var(--border); color: var(--text-secondary); padding: 1px 7px; border-radius: 10px; font-size: 10px; font-weight: 600;">{chat_count}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Empty State
    if not sessions:
        st.markdown(
            """
            <div style="text-align: center; padding: 20px 10px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; margin: 8px 0;">
                <div style="font-size: 1.8rem; margin-bottom: 6px;">💬</div>
                <div style="font-size: 0.82rem; font-weight: 600; color: var(--text-primary); margin-bottom: 2px;">No chats yet</div>
                <div style="font-size: 0.75rem; color: var(--text-secondary);">Start a new conversation above!</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    active_id = st.session_state.get("active_chat_id") or st.session_state.get("conversation_id")
    if not active_id and sessions:
        active_id = sessions[0]["id"]
        st.session_state["active_chat_id"] = active_id
        st.session_state["conversation_id"] = active_id

    for sess in sessions:
        sid = sess["id"]
        title = sess["title"] or "New Chat"
        pinned = bool(sess.get("pinned", 0))
        msg_cnt = sess.get("message_count", 0)

        is_active = (sid == active_id)

        # Style indicators
        pin_prefix = "📌 " if pinned else ""

        c_title, c_edit, c_pin, c_del = st.columns([5.5, 1, 1, 1], gap="small")

        with c_title:
            display_text = f"{pin_prefix}{title}"
            btn_type = "primary" if is_active else "secondary"
            if st.button(display_text, key=f"sel_chat_{sid}", use_container_width=True, help=title, type=btn_type):
                load_chat_session(sid)

        with c_edit:
            if st.button("✏️", key=f"edit_chat_{sid}", help="Rename chat", use_container_width=True):
                st.session_state["editing_chat_id"] = sid if st.session_state.get("editing_chat_id") != sid else None
                st.rerun()

        with c_pin:
            pin_btn_label = "📌" if pinned else "📍"
            if st.button(pin_btn_label, key=f"pin_chat_{sid}", help="Pin / Unpin chat", use_container_width=True):
                toggle_pin_chat(sid)
                st.rerun()

        with c_del:
            if st.button("🗑️", key=f"del_chat_{sid}", help="Delete chat", use_container_width=True):
                st.session_state["deleting_chat_id"] = sid
                st.rerun()

        # Inline Rename Dialog/Input
        if st.session_state.get("editing_chat_id") == sid:
            new_title_input = st.text_input("Rename Title", value=title, key=f"rename_input_{sid}")
            c_save, c_cancel = st.columns([1, 1])
            with c_save:
                if st.button("✓ Save", key=f"save_rename_{sid}", type="primary", use_container_width=True):
                    if new_title_input.strip():
                        update_chat_title(sid, new_title_input.strip())
                        if is_active:
                            st.session_state["chat_title"] = new_title_input.strip()
                    st.session_state["editing_chat_id"] = None
                    st.rerun()
            with c_cancel:
                if st.button("✕ Cancel", key=f"cancel_rename_{sid}", use_container_width=True):
                    st.session_state["editing_chat_id"] = None
                    st.rerun()

        # Inline Delete Confirmation
        if st.session_state.get("deleting_chat_id") == sid:
            st.warning(f"Delete '{title}'? This cannot be undone.")
            c_confirm, c_cancel_del = st.columns([1, 1])
            with c_confirm:
                if st.button("Yes, Delete", key=f"confirm_del_{sid}", type="primary", use_container_width=True):
                    delete_chat_session(sid)
                    st.session_state["deleting_chat_id"] = None
                    if is_active:
                        st.session_state["active_chat_id"] = None
                        st.session_state["chat_title"] = "New Chat"
                        st.session_state["messages"] = []
                    st.rerun()
            with c_cancel_del:
                if st.button("Cancel", key=f"cancel_del_{sid}", use_container_width=True):
                    st.session_state["deleting_chat_id"] = None
                    st.rerun()

        # Metadata Subtitle Line (Message count ONLY - No Timestamps)
        st.markdown(
            f'<div style="font-size: 0.72rem; color: var(--text-secondary); margin-top: -6px; margin-bottom: 10px; padding-left: 4px;">{msg_cnt} messages</div>',
            unsafe_allow_html=True,
        )
