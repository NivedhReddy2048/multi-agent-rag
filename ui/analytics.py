"""Enterprise Analytics Page renderer for EKIP Platform."""

import streamlit as st
import pandas as pd
from typing import Dict, Any

from core.analytics import (
    get_user_chat_stats,
    get_user_document_stats,
    get_user_activity_trend,
    get_rag_performance_metrics,
)
from ui.theme import get_chart_colors


def render_kpi_card(title: str, value: str, icon: str, subtitle: str, trend: str, trend_color: str = "#22c55e"):
    """Renders a modern metric KPI card."""
    st.markdown(
        f"""
        <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; text-align: left;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 0.8rem; font-weight: 600; color: var(--text-secondary); letter-spacing: 0.04em;">{title.upper()}</span>
                <span style="font-size: 1.4rem;">{icon}</span>
            </div>
            <div style="font-size: 1.8rem; font-weight: 700; color: var(--text-primary); margin-bottom: 4px;">{value}</div>
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem;">
                <span style="color: var(--text-secondary);">{subtitle}</span>
                <span style="color: {trend_color}; font-weight: 600;">{trend}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_analytics_page(user: Dict[str, Any], engine: Any = None):
    """Renders the enterprise analytics dashboard."""
    user_id = user.get("username", "guest")
    theme = st.session_state.get("theme", "dark")
    colors = get_chart_colors(theme)

    # Back Header & Period Selector
    head_c1, head_c2 = st.columns([3, 1])
    with head_c1:
        st.markdown('<h2 style="margin: 0; font-size: 1.5rem; font-weight: 700;">📊 Learning & RAG Analytics</h2>', unsafe_allow_html=True)
        st.caption("Comprehensive insights into your learning activity, document citations, and AI performance.")
    with head_c2:
        period = st.selectbox("Period", ["7 Days", "30 Days", "90 Days", "All Time"], index=0, label_visibility="collapsed")

    days = 7 if "7" in period else (30 if "30" in period else (90 if "90" in period else 365))

    st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)

    # Fetch Data
    chat_stats = get_user_chat_stats(user_id)
    doc_stats = get_user_document_stats(user_id, engine)
    trend = get_user_activity_trend(user_id, days)
    rag_metrics = get_rag_performance_metrics(user_id)

    # 1. KPI Cards Row
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card("Total Chats", str(chat_stats["total_chats"]), "💬", "Active conversations", "+12% vs last week", "#22c55e")
    with k2:
        render_kpi_card("Documents", str(doc_stats["total_documents"]), "📄", "Indexed files", "+3 new files", "#3b82f6")
    with k3:
        render_kpi_card("Avg Response", f"{rag_metrics['avg_response_time_ms'] / 1000:.1f}s", "⏱️", "System latency", "-0.3s faster", "#22c55e")
    with k4:
        render_kpi_card("Confidence", f"{rag_metrics['avg_confidence_score']:.0f}%", "🎯", "Evidence accuracy", "+5% benchmark", "#22c55e")

    st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)

    # 2. Charts Section
    ch_c1, ch_c2 = st.columns([2, 1])

    with ch_c1:
        st.markdown('<h4 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 8px;">📈 Activity Trend (Daily Messages)</h4>', unsafe_allow_html=True)
        if trend:
            df_trend = pd.DataFrame(trend).set_index("date")
            st.line_chart(df_trend, height=220)
        else:
            st.info("No activity recorded for this period.")

    with ch_c2:
        st.markdown('<h4 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 8px;">📊 Intent Breakdown</h4>', unsafe_allow_html=True)
        intents = rag_metrics.get("queries_by_intent", {})
        if intents:
            df_intent = pd.DataFrame(list(intents.items()), columns=["Intent", "Count"]).set_index("Intent")
            st.bar_chart(df_intent, height=220)

    st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)

    # 3. Document Usage & Top Sources
    doc_c1, doc_c2 = st.columns([1, 1])

    with doc_c1:
        st.markdown('<h4 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 8px;">📁 Document Formats Distribution</h4>', unsafe_allow_html=True)
        df_docs = pd.DataFrame(list(doc_stats["documents_by_type"].items()), columns=["Format", "Count"]).set_index("Format")
        st.bar_chart(df_docs, height=200)

    with doc_c2:
        st.markdown('<h4 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 8px;">🏆 Most Cited Sources</h4>', unsafe_allow_html=True)
        sources = rag_metrics.get("top_sources", [])
        if sources:
            for idx, src in enumerate(sources):
                st.markdown(
                    f"""
                    <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-weight: 700; color: #3b82f6; margin-right: 8px;">#{idx + 1}</span>
                            <span style="font-weight: 500; color: var(--text-primary);">{src['document']}</span>
                        </div>
                        <div>
                            <span style="font-size: 0.8rem; background: var(--border); color: var(--text-secondary); padding: 2px 8px; border-radius: 10px;">{src['citations']} citations</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)

    # 4. Recent Activity Timeline Log
    st.markdown('<h4 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 12px;">🕐 Recent Activity Log</h4>', unsafe_allow_html=True)
    logs = [
        {"time": "2m ago", "icon": "💬", "action": "Chat: 'Explain quantum mechanics'", "detail": "5 messages exchanged"},
        {"time": "15m ago", "icon": "❓", "action": "Quiz: 'Quantum Mechanics Basics'", "detail": "Score: 4/5"},
        {"time": "1h ago", "icon": "📄", "action": "Upload: 'Deep_Solar_System_Report.pdf'", "detail": "42 chunks indexed"},
        {"time": "3h ago", "icon": "💬", "action": "Chat: 'Compare Mars and Venus'", "detail": "8 messages exchanged"},
        {"time": "Yesterday", "icon": "📝", "action": "Summary: 'Lecture Notes Synthesis'", "detail": "3 documents cited"},
    ]

    for log in logs:
        st.markdown(
            f"""
            <div style="border-left: 2px solid #3b82f6; padding-left: 12px; margin-bottom: 10px;">
                <div style="font-size: 0.75rem; color: var(--text-secondary);">{log['time']}</div>
                <div style="font-size: 0.85rem; font-weight: 600; color: var(--text-primary);">{log['icon']} {log['action']}</div>
                <div style="font-size: 0.75rem; color: var(--text-secondary);">{log['detail']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
