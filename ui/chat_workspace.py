"""Enhanced chat workspace renderer with source citation chips and empty states."""

import streamlit as st
from typing import List, Dict, Any

from ui.chat_sidebar import start_new_chat


def render_source_chips(citations: List[Dict[str, Any]]):
    """Renders expandable source citation chips under assistant messages."""
    if not citations:
        return

    st.markdown('<div style="margin-top: 8px; margin-bottom: 4px; font-size: 0.75rem; font-weight: 600; color: var(--text-secondary);">Retrieved Source Chips:</div>', unsafe_allow_html=True)
    cols = st.columns(min(len(citations), 4))

    for idx, src in enumerate(citations[:4]):
        filename = src.get("source_file", src.get("file", "Document"))
        page = src.get("page", 1)
        snippet = str(src.get("content", ""))[:200]

        with cols[idx]:
            with st.expander(f"📄 {filename[:15]}...", expanded=False):
                st.caption(f"**Page {page}** | Score: {src.get('score', 0.0):.2f}")
                st.markdown(f"> {snippet}...")


def render_empty_chat_state():
    """Renders sleek empty state when no active messages exist."""
    st.markdown(
        """
        <div style="text-align: center; padding: 48px 24px; background: var(--bg-card);
                    border: 1px solid var(--border); border-radius: 16px; margin: 24px 0;">
            <div style="font-size: 2.8rem; margin-bottom: 12px;">💬</div>
            <h3 style="font-size: 1.2rem; font-weight: 700; color: var(--text-primary); margin-bottom: 6px;">
                Start a New Conversation
            </h3>
            <p style="font-size: 0.88rem; color: var(--text-secondary); max-width: 420px; margin: 0 auto 20px auto;">
                Select a chat from the sidebar or choose a Quick Start action from the Student Workspace to begin learning.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, _, c2 = st.columns([2, 3, 2])
    with c1:
        if st.button("➕ Start New Chat", key="btn_empty_start_chat", type="primary", use_container_width=True):
            start_new_chat()
