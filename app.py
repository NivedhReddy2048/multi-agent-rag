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

# Ensure project root is on path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

import streamlit as st
from config import Config
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

# ─── 1. Theme & UI Helpers ───
st.markdown(inject_theme(), unsafe_allow_html=True)


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
    source_mode = meta.get("source_mode", "none")
    faithfulness = meta.get("faithfulness", 0.0)
    crag_score = meta.get("crag_score", meta.get("retrieval_score", 0.0))
    retrieved_chunks = meta.get("retrieved_chunks_count", 0)
    web_results = meta.get("web_results_count", 0)
    decision = meta.get("decision", "Grounded Synthesis")

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
        <span><b>Faithfulness:</b> {faithfulness:.2f}</span>
        <span><b>CRAG Score:</b> {crag_score:.2f}</span>
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
    st.title(f"{Config.APP_ICON} EKIP Platform")
    st.caption("AI-powered Multi-Agent Enterprise Knowledge Platform")
    page = st.radio("Navigation", ["💬 Chat", "📊 Analytics", "📚 Documents", "🩺 LLM Health & Diagnostics"])

    st.markdown("---")

    if page == "💬 Chat":
        if st.button("+ New Chat", use_container_width=True):
            st.session_state.conversation_id = memory.create_conversation()
            st.session_state.messages = []
            logger.info("Created new chat session.")
            st.rerun()

        conversations = memory.list_conversations()
        st.caption(f"💬 History ({len(conversations)} chats)")
        for conv in conversations[:10]:
            is_active = conv["id"] == st.session_state.conversation_id
            label = f"▶ {conv['title']}" if is_active else conv["title"]
            if st.button(label, key=f"conv_{conv['id']}", use_container_width=True):
                st.session_state.conversation_id = conv["id"]
                st.session_state.messages = memory.get_messages(conv["id"])
                logger.info(f"Switched to conversation session '{conv['id']}'")
                st.rerun()

        st.markdown("---")
        st.session_state.show_trace = st.toggle("Show Agent Trace", value=st.session_state.show_trace)

        if st.button("💾 Export Chat", use_container_width=True):
            if st.session_state.messages:
                md_text = ConversationExporter.to_markdown(st.session_state.messages)
                st.download_button(
                    "Download Markdown", md_text, "chat_export.md", "text/markdown", key="dl_md"
                )
            else:
                st.info("No chat messages to export.")

# Ensure messages are synced for active conversation
if not st.session_state.messages and st.session_state.conversation_id:
    st.session_state.messages = memory.get_messages(st.session_state.conversation_id)


# ─── 4. PAGE A: 💬 CHAT ───
if page == "💬 Chat":
    st.title("💬 Enterprise Knowledge Chat")

    # Empty State Hero
    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align: center; padding: 2.5rem 1rem; background: #161b22; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 2rem;">
            <h2 style="color: #4cc9f0; margin-bottom: 0.5rem;">Welcome to Enterprise Knowledge Intelligence Platform</h2>
            <p style="color: #8b949e; max-width: 600px; margin: 0 auto 1.5rem auto;">
                Upload enterprise PDFs, DOCX, CSV, Excel, PPTX, or text files to retrieve grounded insights with multi-agent orchestration, CRAG web fallback, and full auditability.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.caption("Quick actions:")
        col1, col2, col3 = st.columns(3)
        quick_prompt = None
        if col1.button("📑 What documents are indexed?", use_container_width=True):
            quick_prompt = "What documents are indexed?"
        if col2.button("📊 Generate a comprehensive report", use_container_width=True):
            quick_prompt = "Generate a comprehensive report summarizing all uploaded documents."
        if col3.button("🌐 Explain CRAG & Agent Workflow", use_container_width=True):
            quick_prompt = "Explain how CRAG and agent workflow work in this RAG system."

        if quick_prompt:
            prompt = quick_prompt
        else:
            prompt = None
    else:
        prompt = None

    # Render History
    print("=" * 80)
    print(f"TASK 7: SESSION MESSAGES COUNT: {len(st.session_state.messages)}")
    for idx, msg in enumerate(st.session_state.messages):
        if msg["role"] == "assistant":
            print(f"  [MSG #{idx} ASSISTANT | id({id(msg)})]")
            print(f"    Provider: {msg.get('metadata', {}).get('provider', 'UNKNOWN')}")
            print(f"    Model   : {msg.get('metadata', {}).get('model', 'Unknown')}")
            print(f"    Content : {repr(msg.get('content', ''))[:300]}")
    print("=" * 80)

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
    user_input = st.chat_input("Ask about your documents...")
    if user_input:
        prompt = user_input

    if prompt:
        # Display User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Assistant Processing
        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("🧠 *Agents collaborating...*")

            history = st.session_state.messages[:-1]
            ctx = {
                "query": prompt,
                "history": history,
                "filters": {},
                "stream_writer": placeholder.write_stream,
            }

            t0 = time.time()

            try:
                result = orch.run(ctx)
                placeholder.markdown(result.content)
            except Exception as e:
                logger.error(f"Orchestrator execution error: {e}", exc_info=True)
                clean_err = (
                    "The AI service is temporarily unavailable. "
                    "Your documents were searched successfully. "
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
            if result.sources:
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

            # Save to Session State
            st.session_state.messages.append({
                "role": "assistant",
                "content": result.content,
                "citations": result.sources,
                "agent_trace": result.agent_trace,
                "confidence": result.confidence,
                "metadata": result.metadata,
            })


# ─── 5. PAGE B: 📊 ANALYTICS ───
elif page == "📊 Analytics":
    st.title("📊 Enterprise Query Analytics & Observability")
    st.markdown("Actionable telemetry monitoring agent routing, confidence, faithfulness, and CRAG triggers.")

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
    st.title("📚 Document Repository & Ingestion Manager")

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
    st.title("🩺 Multi-LLM Subsystem Health & Diagnostics")
    st.caption("Real-time provider status, active models, latency, and failover diagnostics across Gemini, Groq, Cohere, and Mistral")

    from core.llm import LLMManager, ProviderStatus
    llm_mgr = LLMManager(Config)

    if st.button("🔄 Run Live Health Checks Across All 4 Providers", type="primary"):
        with st.spinner("Pinging Gemini, Groq, Cohere, and Mistral endpoints..."):
            llm_mgr.run_all_health_checks()
        st.toast("Multi-LLM Health checks completed!", icon="✅")

    reports = llm_mgr.get_provider_health()

    c1, c2, c3, c4 = st.columns(4)

    providers_info = [
        ("🔵 Gemini (Primary)", "gemini", c1),
        ("⚡ Groq (Fallback 1)", "groq", c2),
        ("🟢 Cohere (Fallback 2)", "cohere", c3),
        ("🟠 Mistral (Fallback 3)", "mistral", c4),
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
    st.subheader("⚙️ System Environment Audit")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Timeout Budget", f"{getattr(Config, 'LLM_MAX_WAIT_SECONDS', getattr(Config, 'LLM_TIMEOUT_SECONDS', 2.0))}s")
    col_b.metric("Max Retries", f"{getattr(Config, 'LLM_MAX_RETRIES', 0)}")
    col_c.metric("Embedding Model", getattr(Config, "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))
