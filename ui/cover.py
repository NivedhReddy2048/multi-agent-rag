"""Enterprise Cover / Landing Page for EKIP Platform."""

import streamlit as st


def render_cover_page():
    """Renders the full-screen animation-rich enterprise cover page with interactive platform exploration.
    
    On 'Get Started' click: sets st.session_state.auth_view = 'login' and reruns.
    """
    # 1. Initialize cover state defaults
    if "cover_info_open" not in st.session_state:
        st.session_state["cover_info_open"] = False
    if "cover_active_topic" not in st.session_state:
        st.session_state["cover_active_topic"] = "features"

    # Inject background floating orbs, dot grid, and ambient texture
    st.markdown(
        '<div class="orb-1"></div>'
        '<div class="orb-2"></div>'
        '<div class="orb-3"></div>'
        '<div class="dot-grid"></div>'
        '<div class="noise"></div>',
        unsafe_allow_html=True,
    )

    # Injected Cover-Page specific layout, animations, and interactive info panel CSS
    st.markdown(
        """
        <style>
        /* Cover Page Specific Styles & Reset */
        [data-testid="stSidebar"] { display: none !important; }
        header, footer, [data-testid="stHeader"] { visibility: hidden !important; height: 0px !important; }
        
        html, body, .stApp {
            background: linear-gradient(135deg, #0b0d12 0%, #111318 50%, #1a1d26 100%) !important;
            min-height: 100vh !important;
            overflow-x: hidden !important;
        }

        .main .block-container {
            max-width: 1100px !important;
            width: 100% !important;
            padding: 24px 20px 40px 20px !important;
            margin: 0 auto !important;
            position: relative !important;
            z-index: 10 !important;
        }

        /* Top Minimal Navbar */
        .cover-nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 0 24px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            margin-bottom: 32px;
            animation: fadeIn 0.6s ease-out forwards;
        }
        
        .cover-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
        }

        .cover-logo-icon {
            font-size: 28px;
            display: inline-block;
            animation: logoPulse 3s infinite ease-in-out;
        }

        .cover-brand-title {
            font-size: 20px;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: #ffffff;
        }

        .cover-brand-tag {
            font-size: 11px;
            font-weight: 600;
            background: rgba(239, 68, 68, 0.15);
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.3);
            padding: 2px 8px;
            border-radius: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* Nav link button custom styling */
        .cover-nav-btn button {
            background: transparent !important;
            border: none !important;
            color: #94a3b8 !important;
            font-size: 0.875rem !important;
            font-weight: 500 !important;
            padding: 6px 12px !important;
            transition: color 200ms ease, background-color 200ms ease !important;
            box-shadow: none !important;
        }
        .cover-nav-btn button:hover {
            color: #3b82f6 !important;
            background: rgba(59, 130, 246, 0.08) !important;
            border-radius: 6px !important;
        }

        /* Hero Container */
        .cover-hero-container {
            text-align: center;
            max-width: 820px;
            margin: 0 auto;
            padding: 20px 0 10px 0;
        }

        /* Staggered Animations */
        .reveal-badge {
            animation: fadeInUp 0.8s ease-out 0ms forwards;
            opacity: 0;
        }
        .reveal-h1 {
            animation: fadeInUp 0.8s ease-out 200ms forwards;
            opacity: 0;
        }
        .reveal-sub {
            animation: fadeInUp 0.8s ease-out 400ms forwards;
            opacity: 0;
        }
        .reveal-cta {
            animation: fadeInUp 0.8s ease-out 600ms forwards;
            opacity: 0;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(24px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes logoPulse {
            0%, 100% {
                transform: scale(1);
                filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.4));
            }
            50% {
                transform: scale(1.08);
                filter: drop-shadow(0 0 18px rgba(239, 68, 68, 0.75));
            }
        }

        /* Animated Badge */
        .cover-hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 8px 18px;
            border-radius: 30px;
            font-size: 13px;
            font-weight: 500;
            color: #cbd5e1;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        }

        /* Hero Heading & Subtitle */
        .cover-hero-h1 {
            font-size: 48px;
            line-height: 1.15;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: -0.03em;
            margin-bottom: 20px;
            background: linear-gradient(180deg, #ffffff 0%, #cbd5e1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .cover-hero-sub {
            font-size: 18px;
            line-height: 1.6;
            color: #94a3b8;
            font-weight: 400;
            margin-bottom: 32px;
            max-width: 720px;
            margin-left: auto;
            margin-right: auto;
        }

        /* Secondary Ghost Button */
        .cover-cta-secondary button {
            border: 1px solid #1e212b !important;
            background: transparent !important;
            color: #e2e8f0 !important;
            font-weight: 500 !important;
            border-radius: 8px !important;
            transition: all 200ms ease !important;
        }
        .cover-cta-secondary button:hover {
            border-color: #3b82f6 !important;
            color: #ffffff !important;
            box-shadow: 0 0 16px rgba(59, 130, 246, 0.2) !important;
        }

        /* Detailed Info Section Panel */
        .cover-info-panel {
            background: #111318;
            border: 1px solid #1e212b;
            border-radius: 12px;
            padding: 2rem;
            margin-top: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
            animation: fadeInUp 0.4s ease-out forwards;
        }

        .info-panel-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #1e212b;
        }

        .info-panel-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .info-tab-active button {
            background-color: #1e212b !important;
            border: 1px solid #3b82f6 !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            box-shadow: 0 0 12px rgba(59, 130, 246, 0.25) !important;
        }

        .info-tab-inactive button {
            background-color: transparent !important;
            border: 1px solid #1e212b !important;
            color: #94a3b8 !important;
            font-weight: 500 !important;
            border-radius: 8px !important;
        }

        .info-tab-inactive button:hover {
            border-color: #3b82f6 !important;
            color: #ffffff !important;
        }

        .info-close-btn button {
            background: rgba(255, 255, 255, 0.04) !important;
            border: 1px solid #1e212b !important;
            color: #94a3b8 !important;
            border-radius: 6px !important;
            padding: 4px 12px !important;
            font-size: 13px !important;
        }

        .info-close-btn button:hover {
            color: #ef4444 !important;
            border-color: rgba(239, 68, 68, 0.4) !important;
            background: rgba(239, 68, 68, 0.1) !important;
        }

        .info-content-card {
            background: #0b0d12;
            border: 1px solid #1e212b;
            border-radius: 10px;
            padding: 1.75rem;
            color: #e2e8f0;
            line-height: 1.7;
        }

        .info-content-card h1 {
            font-size: 1.5rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 1.25rem;
            border-bottom: 1px solid #1e212b;
            padding-bottom: 0.5rem;
        }

        .info-content-card h2 {
            font-size: 1.1rem;
            font-weight: 600;
            color: #f1f5f9;
            margin-top: 1.25rem;
            margin-bottom: 0.5rem;
        }

        .info-content-card p, .info-content-card li {
            color: #94a3b8;
            font-size: 0.925rem;
        }

        .info-content-card pre {
            background: #111318;
            border: 1px solid #1e212b;
            border-radius: 8px;
            padding: 1rem;
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 0.85rem;
            color: #38bdf8;
            overflow-x: auto;
        }

        /* Highlights Grid */
        .cover-features-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 40px 0 36px 0;
            text-align: left;
            animation: fadeInUp 0.8s ease-out 700ms forwards;
            opacity: 0;
        }

        .cover-feature-card {
            background: rgba(17, 19, 24, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 22px;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .cover-feature-card:hover {
            transform: translateY(-4px);
            border-color: rgba(239, 68, 68, 0.3);
            background: rgba(26, 29, 38, 0.8);
        }

        .feature-icon {
            font-size: 24px;
            margin-bottom: 12px;
        }
        .feature-title {
            font-size: 15px;
            font-weight: 600;
            color: #f1f5f9;
            margin-bottom: 6px;
        }
        .feature-desc {
            font-size: 13px;
            color: #94a3b8;
            line-height: 1.5;
        }

        /* Footer */
        .cover-footer {
            border-top: 1px solid rgba(255, 255, 255, 0.06);
            padding-top: 24px;
            margin-top: 40px;
            text-align: center;
            font-size: 13px;
            color: #64748b;
        }

        /* Responsive Mobile Layout */
        @media (max-width: 768px) {
            .cover-hero-h1 { font-size: 32px !important; }
            .cover-hero-sub { font-size: 15px !important; }
            .cover-features-grid { grid-template-columns: 1fr !important; }
            .cover-info-panel { padding: 1rem !important; }
            .cover-nav { flex-direction: column; gap: 16px; align-items: center; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 1. Top Minimal Navbar with Brand and Interactive Links
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([5, 2, 2, 2])

    with nav_col1:
        st.markdown(
            """
            <div class="cover-brand">
                <span class="cover-logo-icon">🎓</span>
                <span class="cover-brand-title">EKIP Platform</span>
                <span class="cover-brand-tag">Enterprise v2.5</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with nav_col2:
        st.markdown('<div class="cover-nav-btn">', unsafe_allow_html=True)
        if st.button("🚀 Features", key="nav_btn_features", use_container_width=True):
            st.session_state["cover_info_open"] = True
            st.session_state["cover_active_topic"] = "features"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with nav_col3:
        st.markdown('<div class="cover-nav-btn">', unsafe_allow_html=True)
        if st.button("🏗️ Architecture", key="nav_btn_architecture", use_container_width=True):
            st.session_state["cover_info_open"] = True
            st.session_state["cover_active_topic"] = "architecture"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with nav_col4:
        st.markdown('<div class="cover-nav-btn">', unsafe_allow_html=True)
        if st.button("🔒 Security", key="nav_btn_security", use_container_width=True):
            st.session_state["cover_info_open"] = True
            st.session_state["cover_active_topic"] = "security"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    # 2. Hero Section Content
    st.markdown(
        """
        <div class="cover-hero-container">
            <div class="reveal-badge">
                <span class="cover-hero-badge">🎓 Enterprise Educational Intelligence Platform</span>
            </div>
            <h1 class="cover-hero-h1 reveal-h1">
                Master Knowledge with AI-Powered Precision
            </h1>
            <p class="cover-hero-sub reveal-sub">
                EKIP combines multi-agent RAG, deterministic planning, and evidence-driven synthesis to deliver verifiable educational insights and document-grounded quizzes.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. Hero CTA Buttons
    st.markdown('<div class="reveal-cta">', unsafe_allow_html=True)
    col_left, col_btn1, col_btn2, col_right = st.columns([2, 3, 3, 2])

    with col_btn1:
        get_started_clicked = st.button(
            "Get Started →",
            key="cover_btn_get_started",
            use_container_width=True,
            type="primary",
        )

    with col_btn2:
        st.markdown('<div class="cover-cta-secondary">', unsafe_allow_html=True)
        explore_clicked = st.button(
            "📖 Explore EKIP",
            key="cover_btn_explore",
            use_container_width=True,
            type="secondary",
        )
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Button Click Actions
    if get_started_clicked:
        st.session_state["auth_view"] = "login"
        st.rerun()

    if explore_clicked:
        st.session_state["cover_info_open"] = True
        st.session_state["cover_active_topic"] = "features"
        st.rerun()

    # 4. Detailed Info Section (Rendered when cover_info_open is True)
    if st.session_state.get("cover_info_open", False):
        st.markdown('<div class="cover-info-panel">', unsafe_allow_html=True)
        
        # Header Row: Title & Close Button
        hdr_col1, hdr_col2 = st.columns([8, 2])
        with hdr_col1:
            st.markdown(
                '<div class="info-panel-title">📖 About EKIP Platform</div>',
                unsafe_allow_html=True,
            )
        with hdr_col2:
            st.markdown('<div class="info-close-btn">', unsafe_allow_html=True)
            if st.button("✕ Close", key="info_close_btn", use_container_width=True):
                st.session_state["cover_info_open"] = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

        # Tab Navigation Row
        active_topic = st.session_state.get("cover_active_topic", "features")
        tab_col1, tab_col2, tab_col3, tab_space = st.columns([3, 3, 3, 3])

        with tab_col1:
            cls = "info-tab-active" if active_topic == "features" else "info-tab-inactive"
            st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
            if st.button("🚀 Features", key="info_tab_feat", use_container_width=True):
                st.session_state["cover_active_topic"] = "features"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with tab_col2:
            cls = "info-tab-active" if active_topic == "architecture" else "info-tab-inactive"
            st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
            if st.button("🏗️ Architecture", key="info_tab_arch", use_container_width=True):
                st.session_state["cover_active_topic"] = "architecture"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with tab_col3:
            cls = "info-tab-active" if active_topic == "security" else "info-tab-inactive"
            st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
            if st.button("🔒 Security", key="info_tab_sec", use_container_width=True):
                st.session_state["cover_active_topic"] = "security"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

        # Active Topic Card Content
        st.markdown('<div class="info-content-card">', unsafe_allow_html=True)
        if active_topic == "features":
            st.markdown(
                """
# 🚀 Platform Features

## 🤖 Multi-Agent RAG System
Orchestrates CRAG evaluation, verification checks, and structured educational synthesis across specialized agents.

## ⚖️ Balanced Multi-Document Search
Eliminates largest-document bias by enforcing equal chunk quotas across all active corpora. No more 300-page manuals drowning out 5-page cheat sheets.

## 🎯 Deterministic Query Planning
Rule-based intent classification eliminates LLM routing latency. Zero-cost, 100% reproducible query classification.

## 📝 Grounded Quiz Generation
Generates multiple-choice practice quizzes strictly grounded in uploaded source materials with verifiable citations.

## 🔍 Hybrid Retrieval Engine
Dense vector search (ChromaDB) + sparse keyword matching (BM25) with reciprocal rank fusion for maximum relevance.

## 🛡️ Evidence Verification
Scores chunk relevance before synthesis. Halts hallucination early with confidence metrics and grounded refusal.
                """
            )
        elif active_topic == "architecture":
            st.markdown(
                """
# 🏗️ System Architecture

## 📊 Data Ingestion Pipeline
• Universal file parsing: PDF, DOCX, CSV, TXT  
• Semantic chunking: 500 chars with 50-char overlap  
• Metadata enrichment: document_id, filename, page_number, chunk_index  

## 🧠 Dual-Engine Retrieval
```text
┌─────────────┐    ┌─────────────┐
│  ChromaDB   │    │   BM25Okapi │
│   Dense     │ ←→ │   Sparse    │
│  Vectors    │    │  Keywords   │
└──────┬──────┘    └──────┬──────┘
       └────────┬──────────┘
                ▼
         Reciprocal Rank Fusion
                ▼
         Multi-Doc Balancer
                ▼
         Final Context Chunks
```

## 🔄 Execution Flow
User Input → Intent Classification → Target Document Resolution → Execution Plan → Orchestrator → Retrieval → Verification → Synthesis → Response

## 🏢 Multi-Agent Hierarchy
• **OrchestratorAgent** — Workflow coordination  
• **RetrievalAgent** — Dense/BM25 search execution  
• **CRAGAgent** — Corrective RAG evaluation  
• **ValidationAgent** — Constraint & schema validation  
• **SynthesisAgent** — LLM prompt execution  
• **ReportAgent** — Final markdown formatting  
                """
            )
        elif active_topic == "security":
            st.markdown(
                """
# 🔒 Enterprise Security

## 🔐 Password Security
• bcrypt salted hashing — never store plain text  
• Password complexity enforcement (8+ chars, mixed case, digits)  
• Secure password reset with identity verification  

## 🛡️ Session Management
• Remember Me tokens with UUID generation  
• Automatic token invalidation on logout  
• Session state isolation per user  

## 🔏 Data Privacy
• Document content stays in your local vector store  
• No document data sent to LLM providers beyond query context  
• Enterprise Encryption (TLS 1.3) on all connections  

## 📝 Audit & Telemetry
• Query tracing with unique IDs  
• Provider metadata logging  
• Execution span recording for compliance  
                """
            )
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 5. Enterprise Feature Highlights Grid
    st.markdown(
        """
        <div class="cover-features-grid" id="features">
            <div class="cover-feature-card">
                <div class="feature-icon">🤖</div>
                <div class="feature-title">Multi-Agent RAG System</div>
                <div class="feature-desc">Orchestrates CRAG evaluation, verification checks, and structured educational synthesis.</div>
            </div>
            <div class="cover-feature-card">
                <div class="feature-icon">⚖️</div>
                <div class="feature-title">Balanced Multi-Doc Search</div>
                <div class="feature-desc">Eliminates largest-document bias by enforcing equal chunk quotas across all active corpora.</div>
            </div>
            <div class="cover-feature-card">
                <div class="feature-icon">📝</div>
                <div class="feature-title">Grounded Quiz Generation</div>
                <div class="feature-desc">Generates multiple-choice practice quizzes strictly grounded in uploaded source materials.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 6. Footer
    st.markdown(
        """
        <div class="cover-footer" id="security">
            © 2026 EKIP Platform • Enterprise Encryption (TLS 1.3) • Multi-Agent Knowledge Engine v2.5
        </div>
        """,
        unsafe_allow_html=True,
    )
