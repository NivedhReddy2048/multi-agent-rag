"""Enterprise Knowledge Intelligence Platform (EKIP) — Main Application.

Changes made:
- Integrated Loguru logging for UI events and session actions.
- Added granular progress bar callback handling (Upload, Parsing, Chunking, Embedding, Indexing) during document ingestion.
- Added message feedback recording mechanism (thumbs_up / thumbs_down) connecting to ConversationMemory.
- Preserved existing dark theme, layouts, and components.
"""

import os
import sys
import time
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

# Ensure UTF-8 output encoding for Windows consoles to prevent UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def safe_print(*args, **kwargs):
    """Safely print arguments to stdout without crashing on Windows cp1252 character mapping errors."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        file_obj = kwargs.get("file", sys.stdout)
        sep = kwargs.get("sep", " ")
        end = kwargs.get("end", "\n")
        text = sep.join(str(arg) for arg in args)
        safe_text = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
        try:
            file_obj.write(safe_text + end)
        except Exception:
            pass


# Ensure project root is on path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))


import streamlit as st
from config import Config
from core.auth.database import init_db
from core.auth.session import initialize_auth_state, check_remember_me
from core.chat.database import init_chat_db

# Initialize Database & Auth State
init_db()
init_chat_db()
initialize_auth_state()
check_remember_me()

from ui.theme import inject_theme
from core.engine import BaseRAGEngine
from core.memory import ConversationMemory
from core.loader import DocumentLoader
from core.exporters import ConversationExporter
from core.logger import get_logger
from agents.orchestrator import OrchestratorAgent

logger = get_logger("ui.app")

# ─── 0. Environment Validation & Health Check ───
st.set_page_config(
    page_title=Config.APP_TITLE,
    page_icon=Config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    Config.validate()
except Exception as val_err:
    logger.error(f"Configuration validation failed: {val_err}")
    st.error(f"⚠️ Configuration Error: {val_err}")
    st.info("Please set valid API keys in your `.env` file or environment variables.")
    st.stop()

import importlib
import ui.theme
import ui.auth
import ui.shell
import ui.settings
import ui.profile
import ui.chat_sidebar
importlib.reload(ui.theme)
importlib.reload(ui.auth)
importlib.reload(ui.shell)
importlib.reload(ui.settings)
importlib.reload(ui.profile)
importlib.reload(ui.chat_sidebar)

from ui.theme import inject_theme
from ui.cover import render_cover_page
from ui.auth import is_authenticated, render_login_page, render_signup_page, render_forgot_password_page, logout_user
from ui.components import render_sidebar_brand, render_top_header, render_hero_banner, render_quick_starters
from ui.shell import render_top_nav, render_sidebar_controls, render_sidebar_navigation
from ui.settings import render_settings_page
from ui.profile import render_profile_page
from core.auth.database import get_user_theme

# ─── 1. Theme & Authentication Routing Check ───
user_session = st.session_state.get("user")
if user_session and "theme" not in st.session_state:
    st.session_state["theme"] = get_user_theme(user_session["username"])

active_theme = st.session_state.get("theme", "dark")
st.session_state["theme"] = active_theme
st.markdown(inject_theme(active_theme), unsafe_allow_html=True)

if not is_authenticated():
    auth_view = st.session_state.get("auth_view", "cover")
    if auth_view == "cover":
        render_cover_page()
    elif auth_view == "login":
        render_login_page()
    elif auth_view == "forgot":
        render_forgot_password_page()
    elif auth_view == "signup":
        render_signup_page()
    else:
        render_cover_page()
    st.stop()  # Prevent RAG UI from rendering below for unauthenticated users

# ─── Authenticated Post-Login Workspace Setup ───
if "sidebar_collapsed" not in st.session_state:
    st.session_state.sidebar_collapsed = False

from ui.theme import get_sidebar_toggle_css

# 1. Sidebar CSS
st.markdown(get_sidebar_toggle_css(), unsafe_allow_html=True)

# 2. Reopen button (ONLY when sidebar is collapsed)
if st.session_state.get("sidebar_collapsed", False):
    c1, _ = st.columns([1, 30])
    with c1:
        if st.button("☰", key="sb_expand", help="Open sidebar", type="secondary"):
            st.session_state.sidebar_collapsed = False
            st.rerun()



def render_source_card(source: dict) -> str:
    src_file = source.get("source_file", "Unknown")
    page = source.get("page", 1)
    score = source.get("score", 0.0)
    chunk_id = source.get("chunk_id", "")
    content = str(source.get("content", ""))[:350]
    score_info = f" | Score: {score:.2f}" if score else ""
    chunk_info = f" | Chunk: {chunk_id}" if chunk_id else ""
    return f"""
    <div class="source-card">
        <b>📄 {src_file}</b> | Page {page}{score_info}{chunk_info}
        <br/><small style="color: #8b949e;">{content}...</small>
    </div>
    """


def render_confidence_badge(score: int) -> str:
    if score >= 70:
        css = "confidence-high"
        emoji = "🟢"
    elif score >= 40:
        css = "confidence-medium"
        emoji = "🟡"
    else:
        css = "confidence-low"
        emoji = "🔴"
    return f'<span class="confidence-badge {css}">{emoji} Confidence: {score}%</span>'


def render_source_mode_badge(mode: str) -> str:
    mode = str(mode).lower()
    if mode == "documents":
        return '<span style="background: #1f6beb; color: #ffffff; padding: 2px 8px; border-radius: 10px; font-weight: 600; font-size: 0.78rem;">📄 Documents</span>'
    elif mode == "documents+web":
        return '<span style="background: #09b43a; color: #ffffff; padding: 2px 8px; border-radius: 10px; font-weight: 600; font-size: 0.78rem;">📄 + 🌐 Documents & Web</span>'
    elif mode == "web":
        return '<span style="background: #00a8ff; color: #ffffff; padding: 2px 8px; border-radius: 10px; font-weight: 600; font-size: 0.78rem;">🌐 Web Search</span>'
    elif mode in ("general_knowledge", "general"):
        return '<span style="background: #8b5cf6; color: #ffffff; padding: 2px 8px; border-radius: 10px; font-weight: 600; font-size: 0.78rem;">🧠 General Knowledge</span>'
    else:
        return '<span style="background: #6e7681; color: #ffffff; padding: 2px 8px; border-radius: 10px; font-weight: 600; font-size: 0.78rem;">⚠️ No Evidence</span>'


def render_llm_telemetry_pill(meta: Optional[dict]) -> str:
    if not meta or not isinstance(meta, dict):
        meta = {}

    provider = str(meta.get("provider", meta.get("provider_used", "Unknown"))).lower()
    model = str(meta.get("model", "Unknown"))
    latency_ms = meta.get("latency_ms", meta.get("latency", "--"))
    tokens = meta.get("tokens", "--")
    fallback_occurred = meta.get("fallback_occurred", False)
    fallback_chain = meta.get("fallback_chain", [])
    source_mode = meta.get("source_mode", "general_knowledge")
    faithfulness = meta.get("faithfulness", 0.0)
    crag_score = meta.get("crag_score", meta.get("retrieval_score", 0.0))
    retrieved_chunks = meta.get("retrieved_chunks_count", 0)
    web_results = meta.get("web_results_count", 0)

    # Planner Authority & Diagnostic Metadata (Requirement 7)
    exec_plan = meta.get("execution_plan", {})
    planner_strat = meta.get("planner_source_strategy", exec_plan.get("source_strategy", "general_knowledge"))
    runtime_strat = meta.get("runtime_source_strategy", planner_strat)
    was_overridden = "Yes" if meta.get("was_planner_overridden", False) else "No"
    doc_executed = "Yes" if meta.get("document_retrieval_executed", False) else "No"
    override_reason = meta.get("override_reason") or "None"
    decision = meta.get("decision", "General Educational Lesson")

    icon_map = {"gemini": "🔵", "groq": "⚡", "cohere": "🟢", "mistral": "🟠", "none": "⚠️", "unknown": "🤖"}
    icon = icon_map.get(provider, "🤖")

    if fallback_chain:
        chain_str = " → ".join([str(p).capitalize() for p in fallback_chain])
    else:
        chain_str = provider.capitalize() if provider != "unknown" else "Direct"

    fallback_badge_css = "background: #f59e0b; color: #1e1e1e;" if fallback_occurred else "background: #238636; color: #ffffff;"
    mode_badge = render_source_mode_badge(source_mode)

    return f"""
    <div style="margin-top: 10px; padding: 10px 14px; background: #161b22; border-radius: 8px; border: 1px solid #30363d; font-size: 0.82rem; display: flex; flex-wrap: wrap; gap: 14px; align-items: center;">
        <span><b>Provider:</b> {icon} <b>{provider.upper()}</b></span>
        <span><b>Model:</b> <code>{model}</code></span>
        <span><b>Source Mode:</b> {mode_badge}</span>
        <span><b>Planner Strategy:</b> <code>{planner_strat}</code></span>
        <span><b>Runtime Strategy:</b> <code>{runtime_strat}</code></span>
        <span><b>Planner Overridden?</b> {was_overridden}</span>
        <span><b>Doc Retrieval Executed?</b> {doc_executed}</span>
        <span><b>Chunks:</b> {retrieved_chunks} | <b>Web:</b> {web_results}</span>
        <span><b>Decision:</b> <i>{decision}</i></span>
        <span><b>Fallback:</b> <span style="padding: 2px 8px; border-radius: 4px; font-weight: bold; {fallback_badge_css}">{chain_str}</span></span>
    </div>
    """


# ─── 2. Engine & Session Initialization ───
if "engine" not in st.session_state:
    with st.spinner("🚀 Initializing EKIP Engine..."):
        logger.info("Initializing EKIP BaseRAGEngine and agents...")
        st.session_state.engine = BaseRAGEngine(Config)
        st.session_state.memory = ConversationMemory(Config.OBSERVABILITY_DB)
        st.session_state.orchestrator = OrchestratorAgent(
            Config, st.session_state.engine, st.session_state.memory
        )
        st.session_state.conversation_id = st.session_state.memory.create_conversation()
        st.session_state.messages = []
        st.session_state.show_trace = False

engine: BaseRAGEngine = st.session_state.engine
memory: ConversationMemory = st.session_state.memory
orch: OrchestratorAgent = st.session_state.orchestrator

# ─── Health Check Endpoint ───
if st.query_params.get("health") == "1":
    logger.info("Health query params requested.")
    st.json({"status": "ok", "documents": len(engine.list_docs()), "app": Config.APP_TITLE})
    st.stop()


# ─── 3. Sidebar Navigation & Controls ───
with st.sidebar:
    render_sidebar_brand()
    
    doc_cnt = len(engine.list_docs()) or 3
    page = render_sidebar_navigation(doc_cnt)

    st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)
    from ui.chat_sidebar import render_chat_history_sidebar
    user_obj = st.session_state.get("user", {}) or {}
    user_id = user_obj.get("username", "guest")
    render_chat_history_sidebar(user_id)

    st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
    st.session_state.show_trace = st.toggle("Show Agent Trace", value=st.session_state.show_trace)

    if st.button("💾 Export Chat", use_container_width=True):
        if st.session_state.messages:
            md_text = ConversationExporter.to_markdown(st.session_state.messages)
            st.download_button(
                "Download Markdown", md_text, "chat_export.md", "text/markdown", key="dl_md"
            )
        else:
            st.info("No chat messages to export.")

    st.markdown('<div style="border-top: 1px solid rgba(255,255,255,0.06); margin: 12px 0;"></div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size: 11px; color: #22c55e; font-weight: 500; padding: 0 10px;">🟢 System Operational</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-footer-info">User: Student | v2.5</div>', unsafe_allow_html=True)
    st.markdown('<div style="height: 6px;"></div>', unsafe_allow_html=True)
    if st.button("🔒 Logout", use_container_width=True):
        logout_user()

# Ensure messages are synced for active conversation
if not st.session_state.messages and st.session_state.conversation_id:
    st.session_state.messages = memory.get_messages(st.session_state.conversation_id)

# ─── Top Enterprise Navigation Header ───
render_top_nav()

current_pg = st.session_state.get("current_page")
if current_pg == "profile":
    from ui.profile import render_profile_page
    render_profile_page()
    st.stop()
elif current_pg == "settings":
    from ui.settings import render_settings_page
    render_settings_page()
    st.stop()

page_titles = {
    "💬 Chat": "Educational Knowledge Companion",
    "🎓 Student Workspace": "Student Learning Workspace",
    "📊 Analytics": "Query Analytics & Telemetry Dashboard",
    "📚 Documents": "Document Repository & Ingestion Manager",
    "🩺 LLM Health & Diagnostics": "Multi-LLM Health & Subsystem Diagnostics",
}
render_top_header(page_titles.get(page, page), doc_count=len(engine.list_docs()))

# ─── 4. PAGE A: 💬 CHAT ───
if page == "💬 Chat":
    # Empty State Hero & Quick Starters
    if not st.session_state.messages:
        render_hero_banner()
        quick_prompt = render_quick_starters()

        if quick_prompt:
            prompt = quick_prompt
        else:
            prompt = None
    else:
        prompt = None



    # Render History
    safe_print("=" * 80)
    safe_print(f"TASK 7: SESSION MESSAGES COUNT: {len(st.session_state.messages)}")
    for idx, msg in enumerate(st.session_state.messages):
        if msg["role"] == "assistant":
            safe_print(f"  [MSG #{idx} ASSISTANT | id({id(msg)})]")
            safe_print(f"    Provider: {msg.get('metadata', {}).get('provider', 'UNKNOWN')}")
            safe_print(f"    Model   : {msg.get('metadata', {}).get('model', 'Unknown')}")
            safe_print(f"    Content : {repr(msg.get('content', ''))[:300]}")
    safe_print("=" * 80)


    for idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            # Metadata Pill Badges
            badge_html = ""
            if msg.get("confidence") is not None and msg["role"] == "assistant":
                badge_html += render_confidence_badge(msg.get("confidence", 0))

            # CRAG indicator
            trace_list = msg.get("agent_trace", [])
            if any("CRAG" in str(t) or "Web search" in str(t) for t in trace_list):
                badge_html += ' <span class="crag-pill">🌐 Augmented by Web Search</span>'

            if badge_html and msg["role"] == "assistant":
                st.markdown(badge_html, unsafe_allow_html=True)

            if msg["role"] == "assistant" and msg.get("metadata"):
                st.markdown(render_llm_telemetry_pill(msg["metadata"]), unsafe_allow_html=True)

            # Sources Expander
            if msg.get("citations"):
                with st.expander("📎 Retrieved Sources"):
                    for c in msg["citations"]:
                        st.markdown(render_source_card(c), unsafe_allow_html=True)

            # Agent Trace Expander
            if st.session_state.show_trace and msg.get("agent_trace"):
                with st.expander("🔍 Agent Trace"):
                    for t in msg["agent_trace"]:
                        st.markdown(f"- `{t}`")

            # Knowledge Planner Execution Plan Expander
            exec_p = msg.get("metadata", {}).get("execution_plan")
            if st.session_state.show_trace and exec_p:
                with st.expander("🧠 Knowledge Planner Execution Plan"):
                    st.markdown(f"**Intent**: `{exec_p.get('intent', 'N/A')}` | **Difficulty**: `{exec_p.get('difficulty', 'N/A')}`")
                    st.markdown(f"**Selected Sources**: `{exec_p.get('selected_sources', [])}`")
                    st.markdown(f"**Retrieval Strategy**: `{exec_p.get('retrieval_strategy', 'N/A')}` | **Expected Output**: `{exec_p.get('expected_output', 'N/A')}`")
                    st.markdown(f"**Latency Estimate**: `{exec_p.get('estimated_latency', 'N/A')}` | **Cost Estimate**: `{exec_p.get('estimated_cost', 'N/A')}`")
                    if exec_p.get("reasoning_steps"):
                        st.markdown("**Planner Reasoning Steps:**")
                        for step in exec_p["reasoning_steps"]:
                            st.markdown(f"- {step}")

            # Developer-Only Phase 2.3 Knowledge Collection Panel
            col_data = msg.get("metadata", {}).get("knowledge_collection")
            if st.session_state.show_trace and col_data:
                with st.expander("🌐 Phase 2.3 Parallel Knowledge Collection (Developer Panel)"):
                    st.markdown(f"**Total Latency**: `{int(col_data.get('total_latency_ms', 0))} ms` | **Plan ID**: `{col_data.get('execution_plan_id', 'N/A')}`")
                    st.markdown(f"**Requested Sources**: `{col_data.get('sources_requested', [])}`")
                    st.markdown(f"✅ **Completed Sources**: `{col_data.get('sources_completed', [])}`")
                    if col_data.get("sources_failed"):
                        st.markdown(f"❌ **Failed Sources**: `{col_data.get('sources_failed', [])}`")

                    st.markdown("---")
                    st.markdown("#### Retrieved Knowledge Items Breakdown:")
                    results = col_data.get("results", [])
                    if not results:
                        st.info("No items collected.")
                    else:
                        for r_idx, item in enumerate(results):
                            prov = item.get("provider", "unknown")
                            st_type = item.get("source_type", "general")
                            title = item.get("title", "Untitled Item")
                            lat = int(item.get("latency_ms", 0))
                            summary = item.get("summary", item.get("content", ""))[:200]
                            url = item.get("url", "")
                            st.markdown(f"**{r_idx+1}. [{st_type.upper()}] {title}** *(Provider: {prov} | Latency: {lat}ms)*")

                            if summary:
                                st.markdown(f"> {summary}")
                            if url:
                                st.markdown(f"[🔗 Source Link]({url})")

            # Developer-Only Phase 2.4 Knowledge Verification & Evidence Intelligence Panel
            ver_data = msg.get("metadata", {}).get("verified_collection")
            if st.session_state.show_trace and ver_data:
                with st.expander("🔬 Phase 2.4 Knowledge Verification & Evidence Intelligence (Developer Panel)"):
                    st.markdown(f"**Overall Confidence**: `{int(ver_data.get('overall_confidence', 0)*100)}%` | **Overall Agreement**: `{int(ver_data.get('overall_agreement', 0)*100)}%` | **Latency**: `{int(ver_data.get('total_latency_ms', 0))}ms`")
                    st.markdown(f"**Summary**: {ver_data.get('verification_summary', 'N/A')}")

                    if ver_data.get("conflicts"):
                        st.warning(f"⚠️ **Detected Conflicts ({len(ver_data['conflicts'])})**:")
                        for c in ver_data["conflicts"]:
                            st.markdown(f"- **{c.get('source_a', 'Source A')}** vs **{c.get('source_b', 'Source B')}**: {c.get('conflict_type', 'Contradiction')}")

                    if ver_data.get("duplicates"):
                        st.info(f"ℹ️ **Grouped Duplicates ({len(ver_data['duplicates'])})**:")
                        for d in ver_data["duplicates"]:
                            st.markdown(f"- **Canonical**: {d.get('canonical_title')} ({d.get('duplicate_count')} duplicate references)")

                    st.markdown("---")
                    st.markdown("#### Ranked Evidence & Multi-Dimensional Profiles:")
                    v_results = ver_data.get("verified_results", [])
                    for r_idx, v_item in enumerate(v_results):
                        title = v_item.get("title", "Untitled")
                        prov = v_item.get("provider", "unknown")
                        v_score = int(v_item.get("verification_score", 0) * 100)
                        prof = v_item.get("profile", {})

                        st.markdown(f"**{r_idx+1}. {title}** *(Score: {v_score}% | Provider: {prov})*")
                        if prof:
                            st.caption(
                                f"Relevance: {int(prof.get('relevance_score',0)*100)}% | "
                                f"Credibility: {int(prof.get('credibility_score',0)*100)}% | "
                                f"Agreement: {int(prof.get('agreement_score',0)*100)}% | "
                                f"Freshness: {int(prof.get('freshness_score',0)*100)}% | "
                                f"Educational Value: {int(prof.get('educational_value_score',0)*100)}%"
                            )
                        notes = v_item.get("verification_notes", [])
                        if notes:
                            st.markdown("  - *Notes*: " + "; ".join(notes))

            # Phase 3 Status-Aware Educational Response & Guided Learning Render
            edu_res = msg.get("metadata", {}).get("educational_response")
            resp_status = msg.get("metadata", {}).get("response_status")
            if not resp_status and isinstance(edu_res, dict):
                resp_status = edu_res.get("response_status")
            if not resp_status:
                resp_status = "SUCCESS" if (edu_res and edu_res.get("ai_explanation")) else "ERROR"

            if edu_res and resp_status == "SUCCESS":
                with st.expander("🎓 EKIP Educational Response & Guided Learning", expanded=True):
                    def normalize_confidence(val: Any) -> float:
                        if val is None:
                            return 0.0
                        try:
                            f_val = float(val)
                            return round(f_val / 100.0, 4) if f_val > 1.0 else round(max(0.0, min(1.0, f_val)), 4)
                        except (ValueError, TypeError):
                            return 0.0

                    conf_pct = int(normalize_confidence(edu_res.get("confidence", 0)) * 100)
                    raw_agr = edu_res.get("agreement")
                    agr_str = f"{int(float(raw_agr) * 100)}%" if raw_agr is not None else "N/A"
                    provs = ", ".join(edu_res.get("providers_used", [])) or "N/A"
                    st.caption(f"🎯 **Confidence**: {conf_pct}% | 🤝 **Agreement**: {agr_str} | 🌐 **Providers**: `{provs}`")

                    st.markdown("### 🧠 AI Explanation")
                    st.markdown(edu_res.get("ai_explanation", msg.get("content", "")))

                    def format_link(title_text: str, url_val: Optional[str], action_label: str = "Open Link") -> str:
                        if url_val and isinstance(url_val, str) and url_val.startswith(("http://", "https://")):
                            return f"[{title_text}]({url_val})"
                        return title_text

                    has_any_resources = any(
                        bool(edu_res.get(k)) for k in ["uploaded_notes", "research", "videos", "code_examples", "books", "trusted_web", "wikipedia"]
                    )

                    if has_any_resources:
                        st.markdown("---")
                        st.markdown("### 📚 Learn More & Recommended Resources")

                        if edu_res.get("uploaded_notes"):
                            st.markdown("#### 📄 Uploaded Notes & Documents")
                            for n in edu_res["uploaded_notes"]:
                                n_title = n.get('title') or n.get('source_file') or "Uploaded Document"
                                page_info = f" (Page {n.get('page_number', 1)})" if n.get('page_number') else ""
                                n_desc = n.get('content', '')[:200]
                                st.markdown(f"- **📄 {n_title}**{page_info}\n  > {n_desc}...")

                        if edu_res.get("research"):
                            st.markdown("#### 📚 Research Papers")
                            for paper in edu_res["research"]:
                                p_title = paper.get("title", "Research Paper")
                                p_url = paper.get("url")
                                p_link = format_link(p_title, p_url, "Read Paper →")
                                authors = paper.get("authors")
                                auth_str = f" by *{', '.join(authors) if isinstance(authors, list) else authors}*" if authors else ""
                                date_str = f" ({paper.get('published_date')})" if paper.get("published_date") else ""
                                prov_str = f" `[{paper.get('provider', 'arXiv/Scholar')}]`"
                                desc_str = f"\n  > {paper.get('snippet', paper.get('content', ''))[:220]}..." if (paper.get("snippet") or paper.get("content")) else ""
                                st.markdown(f"- **{p_link}**{auth_str}{date_str}{prov_str}{desc_str}")

                        if edu_res.get("videos"):
                            st.markdown("#### 🎥 Recommended Videos")
                            for v in edu_res["videos"]:
                                v_title = v.get("title", "Educational Video")
                                if v_title.startswith("Video: "):
                                    v_title = v_title[7:]
                                v_url = v.get("url") or v.get("metadata", {}).get("video_url")
                                v_link = format_link(v_title, v_url, "Watch Video →")
                                chan = v.get("channel_name") or (v.get("authors")[0] if (isinstance(v.get("authors"), list) and v.get("authors")) else None)
                                chan_str = f" — *Channel: {chan}*" if chan else ""
                                desc = v.get("description") or v.get("content", "")[:180]
                                desc_str = f"\n  > {desc}..." if desc else ""
                                st.markdown(f"- **{v_link}**{chan_str}{desc_str}")

                        if edu_res.get("code_examples"):
                            st.markdown("#### 💻 GitHub Resources")
                            for repo in edu_res["code_examples"]:
                                r_title = repo.get("title", "GitHub Repository")
                                r_url = repo.get("url")
                                r_link = format_link(r_title, r_url, "View Repository →")
                                stars = repo.get("star_count") or repo.get("metadata", {}).get("stars")
                                star_str = f" ⭐ **{stars:,} stars**" if (stars is not None and isinstance(stars, int)) else f" ⭐ {stars} stars" if stars else ""
                                desc = repo.get("content", "")[:200]
                                desc_str = f"\n  > {desc}..." if desc else ""
                                st.markdown(f"- **{r_link}**{star_str}{desc_str}")

                        if edu_res.get("books"):
                            st.markdown("#### 📖 Recommended Books")
                            for b in edu_res["books"]:
                                b_title = b.get("title", "Book Recommendation")
                                b_url = b.get("url")
                                b_link = format_link(b_title, b_url, "View Book →")
                                authors = b.get("authors")
                                auth_str = f" by *{', '.join(authors) if isinstance(authors, list) else authors}*" if authors else ""
                                date_str = f" ({b.get('published_date')})" if b.get("published_date") else ""
                                desc = b.get("content", "")[:200]
                                desc_str = f"\n  > {desc}..." if desc else ""
                                st.markdown(f"- **{b_link}**{auth_str}{date_str}{desc_str}")

                        if edu_res.get("trusted_web") or edu_res.get("wikipedia"):
                            st.markdown("#### 🌐 Reference & Web Sources")
                            all_web = edu_res.get("trusted_web", []) + edu_res.get("wikipedia", [])
                            for w in all_web:
                                w_title = w.get("title", "Web Source")
                                w_url = w.get("url")
                                w_link = format_link(w_title, w_url, "Open Source →")
                                prov_str = f" `[{w.get('provider', 'web')}]`"
                                desc = w.get("snippet") or w.get("content", "")[:200]
                                desc_str = f"\n  > {desc}..." if desc else ""
                                st.markdown(f"- **{w_link}**{prov_str}{desc_str}")

                    if edu_res.get("conflicts"):
                        st.markdown("---")
                        st.warning("#### ⚠️ Conflicting Information Detected")
                        for c in edu_res["conflicts"]:
                            st.markdown(f"- **{c.get('source_a')}** vs **{c.get('source_b')}**: {c.get('conflict_type')}")

                    if edu_res.get("learning_summary"):
                        st.markdown("---")
                        st.success(f"**✅ Final Learning Summary**: {edu_res['learning_summary']}")

                    if edu_res.get("key_takeaways"):
                        st.markdown("#### 📌 Key Takeaways")
                        for kt in edu_res["key_takeaways"]:
                            st.markdown(f"- {kt}")

                    if edu_res.get("important_terms"):
                        st.markdown("#### 📖 Important Terms (Glossary)")
                        for term, defn in edu_res["important_terms"].items():
                            st.markdown(f"- **{term}**: {defn}")

                    if edu_res.get("guided_questions"):
                        st.markdown("---")
                        st.markdown("#### 💡 Guided Learning — Recommended Next Questions")
                        g_cols = st.columns(len(edu_res["guided_questions"]))
                        for g_idx, g_q in enumerate(edu_res["guided_questions"]):
                            if g_cols[g_idx % len(g_cols)].button(f"❓ {g_q}", key=f"gq_{msg.get('id', idx)}_{g_idx}"):
                                st.session_state.next_query = g_q
                                st.rerun()

                    lpath = edu_res.get("learning_path")
                    if lpath and isinstance(lpath, dict) and (lpath.get("prerequisites") or lpath.get("next_topics") or lpath.get("advanced_topics")):
                        st.markdown("---")
                        st.markdown(f"#### 🗺️ Structured Learning Path: *{lpath.get('current_topic', 'Topic')}*")
                        p1, p2, p3, p4 = st.columns(4)
                        with p1:
                            st.markdown("**1. Prerequisites**")
                            for pre in lpath.get("prerequisites", []):
                                st.caption(f"• {pre}")
                        with p2:
                            st.markdown("**2. Current Topic**")
                            st.caption(f"▶ **{lpath.get('current_topic')}**")
                        with p3:
                            st.markdown("**3. Next Topics**")
                            for nxt in lpath.get("next_topics", []):
                                st.caption(f"• {nxt}")
                        with p4:
                            st.markdown("**4. Advanced**")
                            for adv in lpath.get("advanced_topics", []):
                                st.caption(f"• {adv}")
            elif resp_status == "INSUFFICIENT_EVIDENCE":
                st.info("ℹ️ **Notice**: Educational scaffolding suppressed due to insufficient document evidence.")





            # Feedback Options for Assistant Messages
            if msg["role"] == "assistant" and msg.get("id"):
                f_col1, f_col2, _ = st.columns([1, 1, 8])
                if f_col1.button("👍", key=f"fb_up_{msg.get('id', idx)}"):
                    memory.record_feedback(msg["id"], "thumbs_up")
                    st.toast("Feedback recorded: 👍", icon="✅")
                if f_col2.button("👎", key=f"fb_down_{msg.get('id', idx)}"):
                    memory.record_feedback(msg["id"], "thumbs_down")
                    st.toast("Feedback recorded: 👎", icon="📝")

    # User Input Handling
    next_query = st.session_state.pop("next_query", None)
    if next_query:
        prompt = next_query
    else:
        user_input = st.chat_input("Ask about your documents, topics, or concepts...")
        st.markdown('<div class="input-hint-text">↵ to send · Shift + ↵ for new line · Supports PDF, DOCX, TXT</div>', unsafe_allow_html=True)
        if user_input:
            prompt = user_input

    if prompt:
        from ui.chat_sidebar import on_first_message
        from core.chat.database import save_message, increment_message_count, update_chat_preview
        
        on_first_message(prompt)
        active_id = st.session_state.get("active_chat_id")
        if active_id:
            save_message(active_id, "user", prompt)
            increment_message_count(active_id)
            update_chat_preview(active_id, prompt)

        # Display User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Assistant Processing
        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("🧠 *Agents collaborating...*")

            history = st.session_state.messages[:-1]
            # 🧠 Phase 2.2 LangGraph Knowledge Planner Execution (Zero Network / Zero Retrieval)
            from graph.builder import create_ekip_planning_graph
            planning_graph = create_ekip_planning_graph()
            plan_state = planning_graph.invoke({
                "question": prompt,
                "conversation_history": history,
                "execution_mode": "chat_planning",
                "skip_synthesis": True,
            })
            exec_plan = plan_state.get("execution_plan") if isinstance(plan_state, dict) else getattr(plan_state, "execution_plan", None)
            prov_meta = plan_state.get("provider_metadata", {}) if isinstance(plan_state, dict) else getattr(plan_state, "provider_metadata", {})
            edu_meta = prov_meta.get("educational_response") if isinstance(prov_meta, dict) else None
            if not edu_meta:
                edu_meta = plan_state.get("educational_response") if isinstance(plan_state, dict) else getattr(plan_state, "educational_response", None)
            if hasattr(edu_meta, "dict"):
                edu_meta = edu_meta.dict()

            # Record planner telemetry safely
            try:
                memory.record_planner_telemetry(prompt, exec_plan.dict() if exec_plan else {})
            except Exception as tel_err:
                logger.warning(f"Failed to record planner telemetry: {tel_err}")

            ctx = {
                "query": prompt,
                "history": history,
                "filters": {},
                "stream_writer": placeholder.write_stream,
                "execution_plan": exec_plan,
                "educational_response": edu_meta,
                "plan_state": plan_state,
            }

            t0 = time.time()

            try:
                result = orch.run(ctx)
                if exec_plan:
                    result.metadata["execution_plan"] = exec_plan.dict()
                col_meta = prov_meta.get("knowledge_collection") if isinstance(prov_meta, dict) else None
                if col_meta:
                    result.metadata["knowledge_collection"] = col_meta
                    try:
                        memory.record_collection_telemetry(prompt, col_meta)
                    except Exception as col_err:
                        logger.warning(f"Failed to record collection telemetry: {col_err}")
                ver_meta = prov_meta.get("verified_collection") if isinstance(prov_meta, dict) else getattr(plan_state, "verified_collection", None)
                if ver_meta:
                    result.metadata["verified_collection"] = ver_meta
                    try:
                        memory.record_verification_telemetry(prompt, ver_meta)
                    except Exception as ver_err:
                        logger.warning(f"Failed to record verification telemetry: {ver_err}")
                edu_meta = result.metadata.get("educational_response") or edu_meta
                if edu_meta:
                    result.metadata["educational_response"] = edu_meta
                    try:
                        memory.record_synthesis_telemetry(prompt, edu_meta)
                    except Exception as edu_err:
                        logger.warning(f"Failed to record synthesis telemetry: {edu_err}")

                placeholder.markdown(result.content)


            except Exception as e:


                logger.error(f"Orchestrator execution error: {e}", exc_info=True)
                clean_err = (
                    f"The AI service encountered an execution issue: {str(e)}. "
                    "Please try again later."
                )
                from agents.base import AgentResult
                result = AgentResult(
                    content=clean_err,
                    confidence=0,
                    agent_trace=[f"Execution interrupted: {type(e).__name__}"],
                    metadata={
                        "provider": "NONE",
                        "model": "none",
                        "latency_ms": int((time.time() - t0) * 1000),
                        "tokens": 0,
                        "fallback_occurred": False,
                        "fallback_chain": ["NONE"],
                        "error": clean_err,
                        "source_mode": "none",
                    }
                )
                placeholder.markdown(result.content)

            latency = time.time() - t0

            # Render Badges & Metadata
            badge_html = render_confidence_badge(result.confidence)
            if result.metadata.get("crag_used") or any("CRAG" in str(t) or "Web search" in str(t) for t in result.agent_trace):
                badge_html += ' <span class="crag-pill">🌐 Augmented by Web Search</span>'
            st.markdown(badge_html, unsafe_allow_html=True)
            st.markdown(render_llm_telemetry_pill(result.metadata), unsafe_allow_html=True)

            # Sources
            if result.sources and result.metadata.get("response_status") == "SUCCESS":
                with st.expander("📎 Retrieved Sources"):
                    for s in result.sources:
                        st.markdown(render_source_card(s), unsafe_allow_html=True)

            # Trace
            if st.session_state.show_trace:
                with st.expander("🔍 Agent Trace"):
                    for t in result.agent_trace:
                        st.markdown(f"- `{t}`")
                    st.markdown(f"- ⏱️ Total latency: `{latency:.2f}s`")

            # Save to SQLite Memory safely
            try:
                memory.add_message(st.session_state.conversation_id, "user", prompt)
                memory.add_message(
                    st.session_state.conversation_id,
                    "assistant",
                    result.content,
                    agent_trace=result.agent_trace,
                    citations=result.sources,
                    confidence=result.confidence,
                    latency_ms=int(latency * 1000),
                    metadata=result.metadata,
                )
            except Exception as mem_err:
                logger.warning(f"Failed to persist message to SQLite memory: {mem_err}")

            active_id = st.session_state.get("active_chat_id") or st.session_state.get("conversation_id")
            if active_id:
                from core.chat.database import save_message, increment_message_count
                save_message(
                    active_id,
                    "assistant",
                    result.content,
                    citations=result.sources,
                    agent_trace=result.agent_trace,
                    confidence=result.confidence,
                    metadata=result.metadata,
                )
                increment_message_count(active_id)

            # Save to Session State
            st.session_state.messages.append({
                "role": "assistant",
                "content": result.content,
                "citations": result.sources,
                "agent_trace": result.agent_trace,
                "confidence": result.confidence,
                "metadata": result.metadata,
            })
            st.rerun()





# ─── 5. PAGE B: 🎓 STUDENT WORKSPACE ───
elif page == "🎓 Student Workspace":
    from ui.workspace import render_student_workspace
    user_obj = st.session_state.get("user", {}) or {}
    render_student_workspace(user_obj, engine)

    st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📚 Subject Notebooks & Study Tools")
    st.caption("Organize your learning into persistent sessions, subject notebooks, bookmarks, study collections & exports.")

    from core.workspace import workspace_manager, export_engine

    prog = workspace_manager.get_progress()

    # Progress KPI Metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Queries Asked", prog.total_queries)
    m2.metric("Notebooks", prog.notebooks_count)
    m3.metric("Saved Notes", prog.saved_notes_count)
    m4.metric("Bookmarks", f"{prog.read_bookmarks_count}/{prog.bookmarks_count}")
    m5.metric("Collections", prog.collections_count)

    st.markdown("---")

    ws_tab1, ws_tab2, ws_tab3, ws_tab4, ws_tab5, ws_tab6, ws_tab7 = st.tabs([
        "📚 Notebooks",
        "📝 Saved Notes Library",
        "📂 Study Collections",
        "🔖 Bookmarks",
        "🔍 Smart Search",
        "🕒 Sessions & Timeline",
        "🧩 Learning Modules",
    ])


    with ws_tab1:
        st.markdown("### 📚 Subject Notebooks")
        c_nb1, c_nb2 = st.columns([1, 2])
        with c_nb1:
            st.markdown("#### Create New Notebook")
            nb_title = st.text_input("Notebook Title", key="nb_title_in")
            nb_desc = st.text_area("Description", key="nb_desc_in")
            if st.button("Create Notebook", key="btn_create_nb"):
                if nb_title:
                    nb = workspace_manager.create_notebook(nb_title, nb_desc)
                    st.success(f"Created Notebook '{nb.title}'!")
                    st.rerun()

        with c_nb2:
            st.markdown("#### Existing Notebooks")
            notebooks = workspace_manager.list_notebooks()
            if not notebooks:
                st.info("No notebooks created yet.")
            for nb in notebooks:
                with st.expander(f"📚 {nb.title} ({len(nb.notes)} notes)"):
                    st.caption(nb.description or "No description.")
                    if nb.notes:
                        for n in nb.notes:
                            st.markdown(f"- **{n.title}**: {n.ai_explanation[:120]}...")
                        nb_md = export_engine.export_notebook_to_markdown(nb)
                        st.download_button(f"📥 Export Notebook (Markdown)", nb_md, f"{nb.title}.md", "text/markdown", key=f"dl_nb_{nb.id}")

    with ws_tab2:
        st.markdown("### 📝 Saved Notes Library & Exports")
        notes = workspace_manager.get_notes_for_notebook("") + [n for nb in workspace_manager.list_notebooks() for n in nb.notes]
        if not notes:
            st.info("No saved study notes in workspace yet. Ask questions in chat to persist study notes automatically!")
        for n in notes:
            with st.expander(f"📝 {n.title}"):
                st.markdown(f"**Query**: *{n.query}*")
                st.markdown(n.ai_explanation)
                if n.key_takeaways:
                    st.markdown("**Key Takeaways:**")
                    for kt in n.key_takeaways:
                        st.markdown(f"- {kt}")
                exp_col1, exp_col2, exp_col3 = st.columns(3)
                md_bytes = export_engine.export_to_markdown(n)
                txt_bytes = export_engine.export_to_txt(n)
                docx_bytes = export_engine.export_to_docx(n)
                exp_col1.download_button("📥 Markdown (.md)", md_bytes, f"{n.id}.md", "text/markdown", key=f"dl_note_md_{n.id}")
                exp_col2.download_button("📥 Text (.txt)", txt_bytes, f"{n.id}.txt", "text/plain", key=f"dl_note_txt_{n.id}")
                exp_col3.download_button("📥 DOCX (.docx)", docx_bytes, f"{n.id}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", key=f"dl_note_docx_{n.id}")

    with ws_tab3:
        st.markdown("### 📂 Study Collections")
        cols = workspace_manager.list_collections()
        c_col1, c_col2 = st.columns([1, 2])
        with c_col1:
            st.markdown("#### Create Study Collection")
            col_title = st.text_input("Collection Title", key="col_title_in")
            col_cat = st.selectbox("Category", ["Papers", "Videos", "Books", "Vocabulary", "General"], key="col_cat_in")
            if st.button("Create Collection", key="btn_create_col"):
                if col_title:
                    workspace_manager.create_collection(col_title, col_cat)
                    st.success(f"Created Collection '{col_title}'!")
                    st.rerun()

        with c_col2:
            st.markdown("#### Existing Collections")
            if not cols:
                st.info("No study collections created yet.")
            for c in cols:
                with st.expander(f"📂 {c.title} ({c.category})"):
                    st.caption(f"Items count: {len(c.items)}")

    with ws_tab4:
        st.markdown("### 🔖 Resource Bookmarks")
        bm_col1, bm_col2 = st.columns([1, 2])
        with bm_col1:
            st.markdown("#### Add New Bookmark")
            bm_title = st.text_input("Resource Title", key="bm_title_in")
            bm_type = st.selectbox("Resource Type", ["paper", "book", "video", "repo", "article"], key="bm_type_in")
            bm_url = st.text_input("URL", key="bm_url_in")
            if st.button("Add Bookmark", key="btn_add_bm"):
                if bm_title:
                    workspace_manager.add_bookmark(bm_title, bm_type, bm_url)
                    st.success(f"Bookmarked '{bm_title}'!")
                    st.rerun()

        with bm_col2:
            st.markdown("#### Saved Bookmarks")
            bms = workspace_manager.list_bookmarks()
            if not bms:
                st.info("No bookmarks saved yet.")
            for bm in bms:
                st_str = "✅ Read" if bm.is_read else "📖 Unread"
                col_bm1, col_bm2 = st.columns([3, 1])
                col_bm1.markdown(f"- [{bm.title}]({bm.url or '#'}) *({bm.resource_type.upper()})* — `{st_str}`")
                if col_bm2.button("Toggle Read", key=f"tog_bm_{bm.id}"):
                    workspace_manager.toggle_bookmark_read(bm.id)
                    st.rerun()

    with ws_tab5:
        st.markdown("### 🔍 Smart Workspace Search")
        sq = st.text_input("Search workspace notes, notebooks, bookmarks...", key="ws_search_in")
        if sq:
            s_res = workspace_manager.smart_search(sq)
            st.markdown(f"#### Search Results for '{sq}':")
            st.markdown(f"**Notes Found**: {len(s_res['notes'])}")
            for n in s_res["notes"]:
                st.markdown(f"- 📝 **{n['title']}**: *{n['query']}*")
            st.markdown(f"**Notebooks Found**: {len(s_res['notebooks'])}")
            for nb in s_res["notebooks"]:
                st.markdown(f"- 📚 **{nb['title']}**: {nb['description']}")
            st.markdown(f"**Bookmarks Found**: {len(s_res['bookmarks'])}")
            for bm in s_res["bookmarks"]:
                st.markdown(f"- 🔖 **{bm['title']}** ({bm['url']})")

    with ws_tab6:
        st.markdown("### 🕒 Learning Sessions & Timeline")
        s_col1, s_col2 = st.columns([1, 2])
        with s_col1:
            st.markdown("#### Create Learning Session")
            s_title = st.text_input("Session Title", key="sess_title_in")
            s_desc = st.text_area("Session Description", key="sess_desc_in")
            if st.button("Create Session", key="btn_create_sess"):
                if s_title:
                    workspace_manager.create_session(s_title, s_desc)
                    st.success(f"Created Session '{s_title}'!")
                    st.rerun()

        with s_col2:
            st.markdown("#### Learning Timeline")
            sessions = workspace_manager.list_sessions()
            if not sessions:
                st.info("No learning sessions created yet.")
            for s in sessions:
                st.markdown(f"🗓️ **{s.title}** ({s.query_count} queries asked)")
                st.caption(s.description or "No description.")
                st.markdown("---")

    with ws_tab7:
        st.markdown("### 🧩 Adaptive Learning Modules & AI Study Assistant")
        st.caption("Active learning plugins: Flashcards, Quizzes, Mind Maps, Revision Guides, Interview Prep, Coding Practice & Research Assistant.")

        from core.workspace.modules import module_manager
        from core.models.synthesis import EducationalResponse

        mod_list = module_manager.list_modules()
        st.markdown(f"**Registered Learning Modules**: `{len(mod_list)} Active Plugins`")

        sample_resp = EducationalResponse(
            query="Neural Networks and Deep Learning",
            educational_mode="detailed_explanation",
            ai_explanation="Neural networks are computational models composed of layered artificial neurons designed to recognize patterns in data using backpropagation.",
            key_takeaways=[
                "Backpropagation calculates loss gradients via chain rule",
                "Activation functions introduce non-linearity into representations",
                "Deep architectures require regularized weights to prevent overfitting",
            ],
            important_terms={
                "Backpropagation": "Gradient calculation algorithm across network weights",
                "Activation Function": "Non-linear transformation function applied at nodes",
            },
            learning_summary="Deep neural networks learn non-linear representations using gradient descent.",
            confidence=0.92,
            agreement=0.95,
            providers_used=["semantic_scholar", "wikipedia"],
        )

        mod_sub1, mod_sub2, mod_sub3, mod_sub4, mod_sub5, mod_sub6, mod_sub7 = st.tabs([
            "📇 Flashcards",
            "📝 Quiz",
            "🧠 Mind Map",
            "📖 Revision",
            "💼 Interview Prep",
            "💻 Coding Practice",
            "🔬 Research Assistant",
        ])

        with mod_sub1:
            fc_mod = module_manager.get_module("flashcards")
            if fc_mod:
                out = fc_mod.process(sample_resp)
                st.caption(f"🎯 Difficulty Level: `{out.get('difficulty_level', 'medium').upper()}` | Cards Generated: `{out.get('flashcard_count')}`")
                for fc in out.get("flashcards", []):
                    st.markdown(f"**[{fc['type'].upper()}] Card ({fc['difficulty']})**")
                    st.info(f"**Q**: {fc['front']}")
                    st.success(f"**A**: {fc['back']}")
                    st.markdown("---")

        with mod_sub2:
            qz_mod = module_manager.get_module("quizgenerator")
            if qz_mod:
                out = qz_mod.process(sample_resp)
                st.caption(f"🎯 Difficulty: `{out.get('difficulty_level', 'intermediate').upper()}` | Questions: `{out.get('total_questions')}`")
                for idx, q in enumerate(out.get("quiz_questions", []), 1):
                    st.markdown(f"**Question {idx} [{q['type'].upper()}]** ({q['difficulty']})")
                    st.markdown(f"❓ {q['question']}")
                    if "options" in q:
                        for opt in q["options"]:
                            st.caption(f"- {opt}")
                    st.success(f"💡 **Explanation**: {q['explanation']}")
                    st.markdown("---")

        with mod_sub3:
            mm_mod = module_manager.get_module("mindmap")
            cg_mod = module_manager.get_module("conceptgraph")
            if mm_mod:
                out_mm = mm_mod.process(sample_resp)
                st.markdown("#### 🧠 Hierarchical Mind Map Tree")
                st.json(out_mm.get("mind_map_tree", {}))
            if cg_mod:
                out_cg = cg_mod.process(sample_resp)
                st.markdown("#### 🌐 Concept Relationship Graph Nodes")
                st.json(out_cg.get("graph", {}))

        with mod_sub4:
            rev_mod = module_manager.get_module("revisionassistant")
            if rev_mod:
                out = rev_mod.process(sample_resp)
                st.markdown(out.get("one_page_revision", ""))
                st.markdown("---")
                st.markdown("#### ⚡ Exam Cheat Sheet")
                st.code(out.get("cheat_sheet", ""), language="markdown")

        with mod_sub5:
            iv_mod = module_manager.get_module("interviewprep")
            if iv_mod:
                out = iv_mod.process(sample_resp)
                st.markdown("#### 💼 Technical Interview Questions & Rubrics")
                for q in out.get("common_questions", []):
                    st.markdown(f"**Q**: {q['question']}")
                    st.success(f"**Expected Answer**: {q['expected_answer']}")
                    st.warning(f"**Follow-Up Probe**: {q['follow_up']}")
                st.markdown("#### Evaluation Rubric")
                st.json(out.get("evaluation_rubric", {}))

        with mod_sub6:
            cd_mod = module_manager.get_module("codingpractice")
            if cd_mod:
                out = cd_mod.process(sample_resp)
                st.markdown("#### 💻 Programming Exercises & Complexity Analysis")
                for ch in out.get("coding_challenges", []):
                    st.markdown(f"### {ch['title']}")
                    st.caption(f"Time: {ch['time_complexity']} | Space: {ch['space_complexity']}")
                    st.markdown(f"**Problem**: {ch['problem_statement']}")
                    st.code(ch["sample_solution"], language="python")

        with mod_sub7:
            rs_mod = module_manager.get_module("researchassistant")
            if rs_mod:
                out = rs_mod.process(sample_resp)
                st.markdown("#### 🔬 Academic Research Gaps & Future Work")
                st.markdown("**Research Gaps:**")
                for rg in out.get("research_gaps", []):
                    st.markdown(f"- ⚠️ {rg}")
                st.markdown("**Future Directions:**")
                for fw in out.get("future_work", []):
                    st.markdown(f"- 🚀 {fw}")



# ─── 6. PAGE C: 📊 ANALYTICS ───
elif page == "📊 Analytics":
    from ui.analytics import render_analytics_page
    user_obj = st.session_state.get("user", {}) or {}
    render_analytics_page(user_obj, engine)

    st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 🔬 System Observability & Telemetry Details")

    total_q = memory.get_total_queries()
    avg_conf = memory.get_avg_confidence()
    blocked_q = memory.get_blocked_count()
    crag_cnt = memory.get_crag_trigger_count()

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Queries", total_q)
    col2.metric("Avg Confidence", f"{avg_conf:.1f}%")
    col3.metric("Blocked Queries", blocked_q)
    col4.metric("CRAG Triggers", crag_cnt)

    st.markdown("---")

    if total_q == 0:
        st.info("ℹ️ No analytics data available yet. Start chatting to populate telemetry metrics!")
    else:
        # Row 1: Top Keywords & Agent Latency Performance
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("🔥 Top Query Keywords")
            top_kw = memory.get_top_keywords(15)
            if top_kw:
                df_kw = pd.DataFrame(top_kw, columns=["Keyword", "Frequency"])
                st.bar_chart(df_kw.set_index("Keyword"))
            else:
                st.caption("No keywords extracted yet.")

        with col_right:
            st.subheader("⚡ Avg Latency per Intent Route")
            perf = memory.get_agent_performance()
            if perf:
                df_perf = pd.DataFrame(perf)
                df_perf.rename(columns={"intent": "Intent", "avg_latency_ms": "Avg Latency (ms)"}, inplace=True)
                st.bar_chart(df_perf.set_index("Intent")["Avg Latency (ms)"])
            else:
                st.caption("No intent telemetry recorded.")

        st.markdown("---")

        # Row 2: Faithfulness Distribution & Blocked Queries
        col_f, col_b = st.columns(2)

        with col_f:
            st.subheader("🛡️ Faithfulness Distribution")
            faith_scores = memory.get_faithfulness_distribution()
            if faith_scores:
                bins = [0.0, 0.2, 0.4, 0.6, 0.8, 1.01]
                labels = ["0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"]
                counts, _ = np.histogram(faith_scores, bins=bins)
                df_faith = pd.DataFrame({"Score Range": labels, "Count": counts})
                st.bar_chart(df_faith.set_index("Score Range"))
            else:
                st.caption("No faithfulness data available.")

        with col_b:
            st.subheader("🚫 Blocked Queries Log")
            blocked_list = memory.get_blocked_queries(50)
            if blocked_list:
                df_blocked = pd.DataFrame(blocked_list)
                st.dataframe(df_blocked[["timestamp", "query", "reason"]], use_container_width=True)
            else:
                st.success("✅ No queries blocked by hallucination guard!")

        st.markdown("---")

        # Export Section
        st.subheader("📥 Export Telemetry")
        if st.button("Export Telemetry to CSV"):
            all_analytics = memory.get_all_analytics()
            if all_analytics:
                df_export = pd.DataFrame(all_analytics)
                csv_data = df_export.to_csv(index=False)
                st.download_button(
                    label="Download analytics_export.csv",
                    data=csv_data,
                    file_name="query_analytics.csv",
                    mime="text/csv"
                )


# ─── 6. PAGE C: 📚 DOCUMENTS ───
elif page == "📚 Documents":
    from ui.documents import render_documents_page
    user_obj = st.session_state.get("user", {}) or {}
    render_documents_page(user_obj, engine)

    st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📋 System Vector Store Ingestion Manager")

    # Ingestion Card
    with st.expander("📤 Upload & Ingest New Documents", expanded=True):
        uploaded_files = st.file_uploader(
            "Upload files (PDF, DOCX, TXT, CSV, PPTX, XLSX, MD, JSON, PNG, JPEG, TIFF)",
            type=["pdf", "docx", "txt", "csv", "pptx", "xlsx", "md", "json", "png", "jpg", "jpeg", "tiff", "tif"],
            accept_multiple_files=True,
        )

        if uploaded_files:
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            for idx, file in enumerate(uploaded_files):
                status_text.text(f"Uploading file ({idx+1}/{len(uploaded_files)}): '{file.name}'...")
                progress_bar.progress(0.1)

                save_path = Config.UPLOAD_DIR / file.name
                with open(save_path, "wb") as f:
                    f.write(file.getbuffer())

                def update_progress(pct: float, msg: str):
                    progress_bar.progress(pct)
                    status_text.text(msg)

                try:
                    loader = DocumentLoader(
                        chunk_size=Config.CHUNK_SIZE,
                        chunk_overlap=Config.CHUNK_OVERLAP
                    )
                    raw_docs = loader.load_file(str(save_path), parsing_cb=update_progress)
                    chunks = loader.chunk_documents(raw_docs, file.name, chunking_cb=update_progress)
                    res = engine.ingest(str(save_path), chunks, progress_cb=update_progress)
                    st.toast(f"✅ Ingested `{file.name}` ({len(chunks)} chunks)", icon="🎉")
                except Exception as ing_err:
                    logger.error(f"Error ingesting file '{file.name}': {ing_err}")
                    st.error(f"Error ingesting `{file.name}`: {ing_err}")

            status_text.text("Ingestion process complete!")
            progress_bar.progress(1.0)

    st.markdown("---")

    # Indexed Documents List
    st.subheader("📋 Indexed Documents")
    docs = engine.list_docs()

    if not docs:
        st.info("📂 No documents indexed yet. Use the upload box above to add documents to the knowledge base.")
    else:
        for name, info in list(docs.items()):
            cols = st.columns([5, 2, 2, 2, 1])
            cols[0].markdown(f"**📄 {name}**")
            cols[1].caption(f"🧩 {info.get('chunks', 0)} chunks")
            cols[2].caption(f"📑 {info.get('pages', 1)} pages")
            cols[3].caption(f"💾 {info.get('size_mb', 0)} MB")

            if cols[4].button("🗑️", key=f"del_doc_{name}"):
                engine.delete_document(name)
                st.toast(f"Deleted `{name}`")
                st.rerun()

# ─── 7. PAGE D: 🩺 LLM HEALTH & DIAGNOSTICS ───
elif page == "🩺 LLM Health & Diagnostics":
    from ui.llm_health import render_llm_health_page
    user_obj = st.session_state.get("user", {}) or {}
    render_llm_health_page(user_obj, engine)

    st.markdown('<div style="height: 24px;"></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 🔧 Provider Manager & Failover Configuration")

    from core.llm import LLMManager, ProviderStatus
    llm_mgr = LLMManager(Config)

    if st.button("🔄 Run Live Health Checks Across All 4 Providers", type="primary"):
        with st.spinner("Pinging Gemini, Groq, Cohere, and Mistral endpoints..."):
            llm_mgr.run_all_health_checks()
        st.toast("Multi-LLM Health checks completed!", icon="✅")

    reports = llm_mgr.get_provider_health()

    c1, c2, c3, c4 = st.columns(4)

    providers_info = [
        ("⚡ Groq (Primary)", "groq", c1),
        ("🔵 Gemini (Fallback 1)", "gemini", c2),
        ("🟠 Mistral (Fallback 2)", "mistral", c3),
        ("🟢 Cohere (Fallback 3)", "cohere", c4),
    ]

    for title, key, col in providers_info:
        rep = reports.get(key)
        provider_obj = llm_mgr.registry.get_provider(key)
        api_k = provider_obj.api_key if provider_obj else ""
        with col:
            st.subheader(title)
            if rep:
                status_color = "green" if rep.status == ProviderStatus.ONLINE else ("orange" if rep.status in (ProviderStatus.RATE_LIMITED, ProviderStatus.OPEN_CIRCUIT) else "red")
                st.markdown(f"**Status**: :{status_color}[**{rep.status.value}**]")
                st.markdown(f"- **Primary Model**: `{rep.model}`")
                st.markdown(f"- **API Key**: `{'YES (' + str(len(api_k)) + ' chars)' if api_k else 'MISSING'}`")
                st.markdown(f"- **Avg Latency**: `{rep.avg_latency_ms} ms`")
                st.markdown(f"- **Last Success**: `{rep.last_success}`")
                st.markdown(f"- **Failures**: `{rep.failures}`")
                st.markdown(f"- **Success Rate**: `{rep.success_rate}%`")
                st.markdown(f"- **Diagnostic**: {rep.details}")
            else:
                st.error("No health data available.")

    st.markdown("---")
    st.subheader("🌐 Phase 2 Multi-Domain Knowledge Provider Registry")
    st.caption("Categorized infrastructure registry monitoring active and future educational knowledge providers")

    from core.providers import provider_registry
    if st.button("🔍 Run Full Diagnostic Audit Across All 14 Providers", key="audit_all_providers"):
        with st.spinner("Auditing General AI, Search, Extraction, Academic, Media, Books, and Repositories..."):
            provider_reports = provider_registry.run_all_health_checks()
        st.toast("Completed full registry diagnostic audit!", icon="🚀")

    diag_summary = provider_registry.get_diagnostics_summary()

    category_mapping = {
        "General AI": ["gemini", "groq", "cohere", "mistral"],
        "Web Search": ["tavily", "duckduckgo"],
        "Content Extraction & Reader": ["firecrawl", "jina"],
        "Academic Literature & Reference": ["semantic_scholar", "arxiv", "wikipedia"],
        "Educational Media & Books": ["youtube", "google_books"],
        "Repositories & Code": ["github"],
    }

    for cat_name, provider_keys in category_mapping.items():
        with st.expander(f"📁 {cat_name} Providers ({len(provider_keys)})", expanded=True):
            table_data = []
            for name in provider_keys:
                info = diag_summary.get(name, {})
                if not info:
                    continue
                masked_key = Config.get_masked_key(name)
                is_cfg = Config.is_provider_configured(name)
                status_label = info.get("status", "Unknown")
                if is_cfg and status_label in ("Ready (Not yet used)", "Available"):
                    status_display = "🟢 Configured (Ready)"
                elif status_label == "Public API":
                    status_display = "🌐 Public Open Access"
                elif is_cfg:
                    status_display = f"🟡 {status_label}"
                else:
                    status_display = "⚪ Not Configured (Optional)"

                table_data.append({
                    "Provider": info.get("name", name).upper(),
                    "Status": status_display,
                    "Configured": "YES" if is_cfg else "NO",
                    "Credentials / Access": masked_key,
                    "Latency": f"{info.get('latency_ms', 0.0)} ms",
                    "Intended Role": info.get("error") or "Registered (Ready for Phase 2 workflows)",
                })
            st.dataframe(pd.DataFrame(table_data), use_container_width=True)

    st.markdown("---")
    st.subheader("⚙️ System Environment Audit")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Timeout Budget", f"{getattr(Config, 'LLM_MAX_WAIT_SECONDS', getattr(Config, 'LLM_TIMEOUT_SECONDS', 2.0))}s")
    col_b.metric("Max Retries", f"{getattr(Config, 'LLM_MAX_RETRIES', 0)}")
    col_c.metric("Embedding Model", getattr(Config, "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))

    st.markdown("---")
    st.subheader("⚡ Enterprise Performance, Caching & Reliability Dashboard (Phase 2.8)")
    st.caption("Real-time telemetry on multi-level cache hit ratios, background jobs, circuit breakers, and event bus activities.")

    from core.cache import cache_manager
    from core.jobs import job_queue
    from core.reliability import health_monitor

    p_col1, p_col2, p_col3, p_col4 = st.columns(4)

    cache_stats = cache_manager.get_all_stats()
    total_hits = sum(s["hits"] for s in cache_stats.values())
    total_misses = sum(s["misses"] for s in cache_stats.values())
    overall_ratio = round((total_hits / (total_hits + total_misses)) * 100, 2) if (total_hits + total_misses) > 0 else 0.0

    p_col1.metric("Cache Hit Ratio", f"{overall_ratio}%")
    p_col2.metric("Cache Hits", total_hits)
    p_col3.metric("Cache Misses", total_misses)
    p_col4.metric("Active Background Jobs", len(job_queue.list_jobs()))

    st.markdown("#### 💾 Multi-Level Cache Tier Statistics")
    cache_df = pd.DataFrame([
        {
            "Namespace": ns,
            "Current Entries": info["size"],
            "Max Entries": info["max_size"],
            "Hits": info["hits"],
            "Misses": info["misses"],
            "Hit Ratio": f"{info['hit_ratio']}%",
        }
        for ns, info in cache_stats.items()
    ])
    st.dataframe(cache_df, use_container_width=True)

    st.markdown("#### ⚙️ Background Worker Queue Status")
    jobs = job_queue.list_jobs()
    if not jobs:
        st.info("No background jobs recorded in worker queue.")
    else:
        st.dataframe(pd.DataFrame(jobs), use_container_width=True)



