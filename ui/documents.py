"""Enterprise Document Library UI for EKIP Platform."""

import os
import tempfile
import streamlit as st
from typing import Dict, Any, List

from core.documents import (
    get_user_documents,
    save_user_document,
    delete_user_document,
    get_document_chunks,
    reindex_document,
)
from core.loader import DocumentLoader


def format_bytes(size_bytes: int) -> str:
    """Format bytes into readable KB/MB string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def render_chunk_inspector(user_id: str, doc: Dict[str, Any]):
    """Renders chunk inspector panel with prev/next navigation."""
    doc_id = doc["id"]
    filename = doc["filename"]
    chunks = get_document_chunks(doc_id, limit=100)

    st.markdown(f'<div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px;">', unsafe_allow_html=True)
    
    top_c1, top_c2 = st.columns([4, 1])
    with top_c1:
        st.markdown(f"### 📄 {filename} Chunk Inspector")
        st.caption(f"Total Chunks: {len(chunks)} | File Size: {format_bytes(doc.get('size_bytes', 0))} | Status: 🟢 {doc.get('status', 'indexed')}")
    with top_c2:
        if st.button("✕ Close Inspector", key=f"close_insp_{doc_id}"):
            st.session_state["inspect_doc_id"] = None
            st.rerun()

    if not chunks:
        st.info("No text chunks available for this document.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    curr_idx_key = f"chunk_idx_{doc_id}"
    if curr_idx_key not in st.session_state:
        st.session_state[curr_idx_key] = 0

    curr_idx = st.session_state[curr_idx_key]
    curr_idx = max(0, min(curr_idx, len(chunks) - 1))
    chk = chunks[curr_idx]

    nav_c1, nav_c2, nav_c3 = st.columns([1, 3, 1])
    with nav_c1:
        if st.button("← Previous", key=f"prev_chk_{doc_id}", disabled=(curr_idx == 0)):
            st.session_state[curr_idx_key] -= 1
            st.rerun()
    with nav_c2:
        st.markdown(f'<div style="text-align: center; font-weight: 600;">Chunk {curr_idx + 1} of {len(chunks)} • Page {chk.get("page_number", 1)} • {chk.get("char_count", 0)} chars</div>', unsafe_allow_html=True)
    with nav_c3:
        if st.button("Next →", key=f"next_chk_{doc_id}", disabled=(curr_idx == len(chunks) - 1)):
            st.session_state[curr_idx_key] += 1
            st.rerun()

    st.markdown(
        f"""
        <div style="background: #0b0d12; border: 1px solid #1e212b; border-radius: 8px; padding: 16px; font-family: monospace; font-size: 0.82rem; color: #e2e8f0; white-space: pre-wrap; word-break: break-word; max-height: 300px; overflow-y: auto; margin-top: 12px;">
{chk.get('text', '')}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)


def render_documents_page(user: Dict[str, Any], engine: Any = None):
    """Renders main Enterprise Document Library."""
    user_id = user.get("username", "guest")

    st.markdown('<h2 style="margin: 0 0 4px 0; font-size: 1.5rem; font-weight: 700;">📁 Document Library</h2>', unsafe_allow_html=True)
    st.caption("Upload, manage, inspect, and organize your study materials for AI-powered RAG retrieval.")
    st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)

    # 1. Upload Dropzone Area
    with st.expander("📤 Drag & Drop Upload Zone", expanded=False):
        uploaded_files = st.file_uploader(
            "Upload study materials (PDF, DOCX, CSV, TXT)",
            accept_multiple_files=True,
            type=["pdf", "docx", "csv", "txt"],
            key="doc_uploader_input",
        )
        if uploaded_files:
            loader = DocumentLoader()
            for u_file in uploaded_files:
                with st.spinner(f"Indexing '{u_file.name}'..."):
                    # Save to temp file
                    ext = os.path.splitext(u_file.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                        tmp.write(u_file.getvalue())
                        tmp_path = tmp.name

                    try:
                        docs = loader.load_file(tmp_path)
                        chunks = loader.chunk_documents(docs, u_file.name)
                        save_user_document(
                            user_id=user_id,
                            filename=u_file.name,
                            title=u_file.name.rsplit(".", 1)[0].replace("_", " ").title(),
                            doc_type=ext.replace(".", "").lower(),
                            size_bytes=len(u_file.getvalue()),
                            chunks=chunks,
                        )
                        st.toast(f"✅ Indexed '{u_file.name}' ({len(chunks)} chunks)", icon="📄")
                    except Exception as err:
                        st.error(f"Failed to process '{u_file.name}': {err}")
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
            st.rerun()

    # 2. Search & Filter Bar
    ctrl_c1, ctrl_c2 = st.columns([3, 1])
    with ctrl_c1:
        search_query = st.text_input("🔍 Search documents...", placeholder="Filter by filename...", key="doc_search_in")
    with ctrl_c2:
        filter_type = st.selectbox("Format Filter", ["All Formats", "PDF", "DOCX", "CSV", "TXT"], key="doc_format_filter")

    docs = get_user_documents(user_id)

    # Filter logic
    if search_query:
        docs = [d for d in docs if search_query.lower() in d["filename"].lower() or search_query.lower() in d["title"].lower()]
    if filter_type != "All Formats":
        docs = [d for d in docs if d["type"].lower() == filter_type.lower()]

    # 3. Active Chunk Inspector check
    active_insp_id = st.session_state.get("inspect_doc_id")
    if active_insp_id:
        insp_doc = next((d for d in docs if d["id"] == active_insp_id), None)
        if insp_doc:
            render_chunk_inspector(user_id, insp_doc)

    # 4. Deleting state check
    deleting_id = st.session_state.get("deleting_doc_id")
    if deleting_id:
        del_doc = next((d for d in docs if d["id"] == deleting_id), None)
        if del_doc:
            st.warning(f"⚠️ Are you sure you want to delete '{del_doc['filename']}'? This will remove all {del_doc['chunk_count']} chunks.")
            c1, c2, _ = st.columns([1, 1, 3])
            with c1:
                if st.button("Confirm Delete", type="primary", key="btn_confirm_del_doc"):
                    delete_user_document(user_id, deleting_id)
                    st.session_state["deleting_doc_id"] = None
                    st.toast(f"Deleted '{del_doc['filename']}'", icon="🗑️")
                    st.rerun()
            with c2:
                if st.button("Cancel", key="btn_cancel_del_doc"):
                    st.session_state["deleting_doc_id"] = None
                    st.rerun()

    # 5. Empty State
    if not docs:
        st.markdown(
            """
            <div style="text-align: center; padding: 48px 24px; background: var(--bg-card);
                        border: 1px solid var(--border); border-radius: 16px; margin: 24px 0;">
                <div style="font-size: 2.8rem; margin-bottom: 12px;">📁</div>
                <h3 style="font-size: 1.2rem; font-weight: 700; color: var(--text-primary); margin-bottom: 6px;">
                    Your Document Library is Empty
                </h3>
                <p style="font-size: 0.88rem; color: var(--text-secondary); max-width: 440px; margin: 0 auto 20px auto;">
                    Upload PDFs, DOCX, CSV, or TXT files to build your personal knowledge base for AI-powered learning.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # 6. Document Cards Grid (4 columns)
    st.markdown(f'<div style="font-size: 0.85rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 12px;">SHOWING {len(docs)} DOCUMENTS</div>', unsafe_allow_html=True)
    
    rows = [docs[i:i + 4] for i in range(0, len(docs), 4)]

    for row in rows:
        cols = st.columns(4)
        for idx, doc in enumerate(row):
            with cols[idx]:
                doc_id = doc["id"]
                filename = doc["filename"]
                doc_type = doc["type"].upper()
                chunk_cnt = doc["chunk_count"]
                size_str = format_bytes(doc.get("size_bytes", 0))

                icon = "📄" if doc_type == "PDF" else ("📝" if doc_type == "DOCX" else ("📊" if doc_type == "CSV" else "📃"))

                st.markdown(
                    f"""
                    <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin-bottom: 12px;">
                        <div style="font-size: 1.8rem; margin-bottom: 8px;">{icon}</div>
                        <div style="font-size: 0.9rem; font-weight: 600; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{filename}">
                            {filename}
                        </div>
                        <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 4px; margin-bottom: 12px;">
                            {chunk_cnt} chunks • {size_str}<br>
                            <span style="color: #22c55e;">🟢 Indexed</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                c_v, c_d = st.columns([3, 1])
                with c_v:
                    if st.button("View", key=f"view_doc_{doc_id}", use_container_width=True):
                        st.session_state["inspect_doc_id"] = doc_id
                        st.rerun()
                with c_d:
                    if st.button("🗑️", key=f"del_doc_{doc_id}", help="Delete document"):
                        st.session_state["deleting_doc_id"] = doc_id
                        st.rerun()
