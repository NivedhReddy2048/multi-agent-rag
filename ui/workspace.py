"""Enterprise Student Workspace & Dashboard UI for EKIP Platform."""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, List

from core.auth.database import get_user_preferences, update_user_preferences
from core.chat.database import get_chat_sessions, create_chat_session
from ui.chat_sidebar import format_relative_time, load_chat_session, start_new_chat


def render_welcome_card(user: Dict[str, Any], doc_count: int, chat_count: int):
    """Renders dismissible personalized welcome header card."""
    first_name = user.get("first_name", "Student")
    user_id = user.get("username", "guest")

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, rgba(59,130,246,0.08) 0%, rgba(139,92,246,0.08) 100%);
                    border: 1px solid rgba(59,130,246,0.25);
                    border-radius: 16px; padding: 24px; margin-bottom: 24px; position: relative;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h2 style="margin: 0 0 8px 0; font-size: 1.5rem; font-weight: 700; color: var(--text-primary);">
                        👋 Welcome back, {first_name}!
                    </h2>
                    <p style="margin: 0 0 16px 0; font-size: 0.9rem; color: var(--text-secondary);">
                        You have <b style="color: var(--accent);">{doc_count}</b> documents indexed and <b style="color: #3b82f6;">{chat_count}</b> active conversations.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, _ = st.columns([2, 2, 1, 5])
    with c1:
        if st.button("Continue Last Chat →", key="btn_w_cont_chat", type="primary", use_container_width=True):
            sessions = get_chat_sessions(user_id)
            if sessions:
                load_chat_session(sessions[0]["id"])
            else:
                start_new_chat()
    with c2:
        if st.button("Upload Documents →", key="btn_w_up_docs", use_container_width=True):
            st.session_state["active_nav"] = "📁 Documents"
            st.rerun()
    with c3:
        if st.button("✕ Dismiss", key="btn_w_dismiss", help="Hide welcome card"):
            update_user_preferences(user_id, show_welcome_card=0)
            st.rerun()

    st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)


QUICK_ACTIONS = [
    {"icon": "📖", "label": "Explain a Concept", "subtitle": "Deep-dive explanations with source verification", "intent": "CONCEPT_EXPLANATION", "prefill": None, "auto_submit": False},
    {"icon": "🌐", "label": "Explore Trusted Sources", "subtitle": "Search verified educational web knowledge", "intent": "WEB_SEARCH", "prefill": None, "auto_submit": False},
    {"icon": "📝", "label": "Summarize My Notes", "subtitle": "Comprehensive summary across all uploaded documents", "intent": "DOCUMENT_SUMMARIZATION", "prefill": "Summarize my uploaded documents", "auto_submit": True},
    {"icon": "🎬", "label": "Recommend Videos", "subtitle": "Curated video concepts and lecture recommendations", "intent": "GENERAL_KNOWLEDGE", "prefill": None, "auto_submit": False},
    {"icon": "⚖️", "label": "Compare Two Topics", "subtitle": "Side-by-side comparative analysis", "intent": "COMPARISON", "prefill": None, "auto_submit": False},
    {"icon": "📚", "label": "Create Study Notes", "subtitle": "Structured revision notes and key terminology", "intent": "CONCEPT_EXPLANATION", "prefill": None, "auto_submit": False},
    {"icon": "🔬", "label": "Find Research Papers", "subtitle": "Retrieve academic literature abstracts and citations", "intent": "WEB_SEARCH", "prefill": None, "auto_submit": False},
    {"icon": "❓", "label": "Practice Quiz", "subtitle": "Generate 5 document-grounded multiple-choice questions", "intent": "QUIZ_GENERATION", "prefill": "Generate a practice quiz from my documents", "auto_submit": True},
]


def handle_quick_action(action: dict, user_id: str, doc_count: int):
    """Handle click on a quick start action card."""
    if action["intent"] in ("DOCUMENT_SUMMARIZATION", "QUIZ_GENERATION") and doc_count == 0:
        st.warning("📁 Please upload documents first to use this feature.")
        st.session_state["active_nav"] = "📚 Documents"
        st.rerun()
        return

    session_id = create_chat_session(user_id, action["label"])
    st.session_state["active_chat_id"] = session_id
    st.session_state["conversation_id"] = session_id
    st.session_state["chat_title"] = action["label"]
    st.session_state["messages"] = []
    st.session_state["intent_override"] = action["intent"]
    st.session_state["prefill_prompt"] = action["prefill"]
    st.session_state["auto_submit"] = action["auto_submit"]

    if action["auto_submit"] and action["prefill"]:
        st.session_state["next_query"] = action["prefill"]

    st.session_state["active_nav"] = "💬 Chat"
    st.session_state["nav_page"] = "💬 Chat"
    st.rerun()


def render_quick_start_grid(user_id: str = "guest", doc_count: int = 0):
    """Renders 2x4 grid of enterprise quick-start action cards."""
    st.markdown('<h3 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 12px;">🚀 Quick Start Actions</h3>', unsafe_allow_html=True)

    row1 = QUICK_ACTIONS[:4]
    row2 = QUICK_ACTIONS[4:]

    for row in (row1, row2):
        cols = st.columns(4)
        for idx, act in enumerate(row):
            with cols[idx]:
                st.markdown(
                    f"""
                    <div style="background: var(--bg-card); border: 1px solid var(--border);
                                border-radius: 12px; padding: 16px 12px; text-align: center;
                                transition: all 0.2s ease; height: 100%;">
                        <div style="font-size: 1.6rem; margin-bottom: 6px;">{act['icon']}</div>
                        <div style="font-size: 0.88rem; font-weight: 600; color: var(--text-primary); margin-bottom: 2px;">{act['label']}</div>
                        <div style="font-size: 0.72rem; color: var(--text-secondary);">{act['subtitle']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(f"Start: {act['label']}", key=f"qs_{act['label'].replace(' ', '_')}", use_container_width=True):
                    handle_quick_action(act, user_id, doc_count)


def render_recent_activity(user_id: str):
    """Renders recent chat activity card."""
    st.markdown('<h4 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 8px;">📊 Recent Activity</h4>', unsafe_allow_html=True)
    sessions = get_chat_sessions(user_id)[:4]

    if not sessions:
        st.markdown('<div style="font-size: 0.8rem; color: var(--text-secondary); padding: 12px;">No recent chat history found.</div>', unsafe_allow_html=True)
        return

    for sess in sessions:
        sid = sess["id"]
        title = sess["title"] or "New Chat"
        msg_cnt = sess.get("message_count", 0)
        time_str = format_relative_time(sess.get("updated_at"))

        c1, c2 = st.columns([4, 1])
        with c1:
            if st.button(f"💬 {title}", key=f"dash_rec_{sid}", use_container_width=True, help=title):
                load_chat_session(sid)
        with c2:
            st.caption(f"{msg_cnt} msgs • {time_str}")


def normalize_workspace_docs(raw_docs: Any) -> List[Any]:
    """Defensively normalizes raw document structures into a flat List[Any]."""
    if raw_docs is None:
        return []

    if isinstance(raw_docs, (list, tuple)):
        return list(raw_docs)

    if isinstance(raw_docs, dict):
        wrapper_keys = ("documents", "docs", "items", "results", "data")
        for key in wrapper_keys:
            if key in raw_docs and isinstance(raw_docs[key], (list, tuple)):
                return list(raw_docs[key])

        result = []
        for key, val in raw_docs.items():
            if isinstance(val, dict):
                has_name = any(k in val for k in ("filename", "name", "original_filename", "title"))
                if not has_name and isinstance(key, str):
                    val_copy = dict(val)
                    val_copy["filename"] = key
                    result.append(val_copy)
                else:
                    result.append(val)
            else:
                result.append(val)
        return result

    return [raw_docs]


def get_workspace_doc_name(doc: Any) -> str:
    """Extracts document filename/title from dict or object with priority lookup."""
    if doc is None:
        return "Untitled document"

    if isinstance(doc, str):
        return doc.strip() if doc.strip() else "Untitled document"

    name_keys = ("filename", "name", "original_filename", "title")

    if isinstance(doc, dict):
        for k in name_keys:
            val = doc.get(k)
            if val and isinstance(val, str) and val.strip():
                return val.strip()
        return "Untitled document"

    for k in name_keys:
        val = getattr(doc, k, None)
        if val and isinstance(val, str) and val.strip():
            return val.strip()

    str_val = str(doc)
    if str_val and not str_val.startswith("<"):
        return str_val

    return "Untitled document"


def render_quick_access_docs(docs: List[Any]):
    """Renders quick access uploaded documents list."""
    st.markdown('<h4 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 8px;">📁 Quick Access Documents</h4>', unsafe_allow_html=True)

    if not docs:
        st.markdown('<div style="font-size: 0.8rem; color: var(--text-secondary); padding: 12px;">No documents uploaded yet.</div>', unsafe_allow_html=True)
        return

    for doc in docs[:4]:
        doc_name = get_workspace_doc_name(doc)
        ext = doc_name.split(".")[-1].lower() if "." in doc_name else ""
        icon = "📄" if ext == "pdf" else ("📝" if ext in ("docx", "doc", "txt") else ("📊" if ext in ("csv", "xlsx") else "📁"))

        st.markdown(
            f"""
            <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px; margin-bottom: 6px; display: flex; align-items: center; justify-content: space-between;">
                <span style="font-size: 0.82rem; font-weight: 500; color: var(--text-primary);">{icon} {doc_name}</span>
                <span style="font-size: 0.7rem; color: var(--text-secondary);">Indexed</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_student_workspace(user: Dict[str, Any], engine: Any):
    """Main rendering entrypoint for Enterprise Student Workspace."""
    user_id = user.get("username", "guest")
    prefs = get_user_preferences(user_id)
    show_welcome = bool(prefs.get("show_welcome_card", 1))

    raw_docs = engine.list_docs() if hasattr(engine, "list_docs") else []
    docs = normalize_workspace_docs(raw_docs)
    doc_count = len(docs)
    sessions = get_chat_sessions(user_id)
    chat_count = len(sessions)

    # 1. Welcome Card
    if show_welcome:
        render_welcome_card(user, doc_count, chat_count)

    # 2. Activity & Quick Access Split
    col_act, col_docs = st.columns([1, 1])
    with col_act:
        render_recent_activity(user_id)
    with col_docs:
        render_quick_access_docs(docs)

    st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)

    # 3. Quick Start Actions Grid
    render_quick_start_grid(user_id, doc_count)

