"""Reusable Enterprise UI Components for EKIP Platform."""

import streamlit as st
from typing import Optional


def render_sidebar_brand():
    """Render enterprise brand header inside sidebar with collapse button."""
    col_brand, col_collapse = st.columns([5, 1])
    with col_brand:
        html = (
            '<div class="sidebar-brand">'
            '<div class="sidebar-brand-logo">🎓</div>'
            '<div>'
            '<div class="sidebar-brand-title">EKIP Platform</div>'
            '<div class="sidebar-brand-sub">Educational Knowledge Intelligence</div>'
            '</div>'
            '</div>'
        )
        st.markdown(html, unsafe_allow_html=True)
    with col_collapse:
        if st.button("◀", key="sidebar_header_collapse", help="Collapse Sidebar", type="secondary"):
            st.session_state["sidebar_collapsed"] = True
            st.rerun()


def render_top_header(page_name: str, doc_count: int = 3):
    """Render top application space without breadcrumb headers or extra deploy/search buttons."""
    pass


def render_hero_banner():
    """Render enterprise hero card according to design specifications (no meta pills, sleek knowledge pipeline)."""
    html = (
        '<div class="hero-card">'
        '<div class="hero-lbl">AI LEARNING INFRASTRUCTURE</div>'
        '<div class="hero-title">Educational Knowledge Companion</div>'
        '<div class="hero-sub">Your AI-powered learning infrastructure. Ask complex questions, retrieve verified knowledge, synthesize document insights, and generate practice quizzes.</div>'
        '<div class="hero-pipeline-container">'
        '<div class="hero-pipeline-item"><span class="hero-pipeline-icon">🎯</span><span>Ask Question</span></div>'
        '<div class="hero-pipeline-arrow">→</div>'
        '<div class="hero-pipeline-item"><span class="hero-pipeline-icon">🌐</span><span>Multi-Source Retrieval</span></div>'
        '<div class="hero-pipeline-arrow">→</div>'
        '<div class="hero-pipeline-item"><span class="hero-pipeline-icon">✓</span><span>Verification & Evidence</span></div>'
        '<div class="hero-pipeline-arrow">→</div>'
        '<div class="hero-pipeline-item"><span class="hero-pipeline-icon">🎓</span><span>Grounded Learning</span></div>'
        '</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_quick_starters() -> Optional[str]:
    """Render 8 quick start action cards in a 2-column enterprise grid."""
    st.markdown('<div class="quick-start-lbl" style="font-size: 11px; font-weight: 700; color: var(--text-secondary); letter-spacing: 0.05em; margin-bottom: 12px;">QUICK START ACTIONS</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    selected_prompt = None

    with col1:
        if st.button("📐  Explain a Concept\nDeep-dive explanations with source verification", use_container_width=True, key="qs_explain"):
            selected_prompt = "Explain the core concepts of Transformer architectures in Machine Learning."
        
        if st.button("📝  Summarize My Notes\nComprehensive summary across all uploaded study documents", use_container_width=True, key="qs_summarize"):
            selected_prompt = "Generate a comprehensive summary of my uploaded study notes."

        if st.button("📊  Compare Two Topics\nSide-by-side comparative analysis of educational concepts", use_container_width=True, key="qs_compare"):
            selected_prompt = "Compare Supervised Learning vs Unsupervised Learning with examples."

        if st.button("🔬  Find Research Papers\nRetrieve academic literature abstracts and citations", use_container_width=True, key="qs_research"):
            selected_prompt = "Find key research paper abstracts on Retrieval-Augmented Generation (RAG)."

    with col2:
        if st.button("🌐  Explore Trusted Sources\nSearch verified educational web knowledge and articles", use_container_width=True, key="qs_web"):
            selected_prompt = "Search trusted web sources on quantum computing advancements."

        if st.button("🎬  Recommend Videos\nCurated video concepts and lecture recommendations", use_container_width=True, key="qs_videos"):
            selected_prompt = "Recommend top learning video concepts for understanding neural networks."

        if st.button("📋  Create Study Notes\nStructured revision notes and key terminology breakdown", use_container_width=True, key="qs_notes"):
            selected_prompt = "Create structured study notes for my AI & Machine Learning preparation."

        if st.button("❓  Practice Quiz\nGenerate 5 document-grounded multiple-choice questions", use_container_width=True, key="qs_quiz"):
            selected_prompt = "Generate 5 practice quiz questions based on my indexed documents."

    return selected_prompt
