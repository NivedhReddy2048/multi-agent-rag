"""Settings page component with Profile management and Appearance theme options."""

import base64
import streamlit as st
from typing import Dict, Any, Optional

from core.auth.database import (
    update_user_profile,
    update_user_theme,
    get_user_by_username,
)
from ui.shell import get_avatar_html, get_user_initials


def render_settings_page():
    """Render full-page settings component with Profile and Appearance tabs."""
    user = st.session_state.get("user")
    if not user:
        st.warning("Please sign in to access settings.")
        return

    # Refresh user object from DB to ensure accurate data
    fresh_user = get_user_by_username(user["username"])
    if fresh_user:
        user = fresh_user
        st.session_state["user"] = fresh_user

    # ─── Top Bar Navigation (Back Button) ───
    col_back, _ = st.columns([1, 10])
    with col_back:
        if st.button("← Back", key="settings_back", help="Return to Chat"):
            st.session_state["current_page"] = "chat"
            st.rerun()

    st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)

    # ─── Page Header ───
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 24px; font-weight: 800; color: var(--text-primary); margin-bottom: 4px;">
                ⚙️ Platform Settings
            </h1>
            <p style="font-size: 13px; color: var(--text-secondary);">
                Customize your user profile and interface theme preferences.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Active Tab Selection
    default_tab_idx = 1 if st.session_state.get("settings_active_tab") == "Appearance" else 0
    tab_profile, tab_appearance, tab_info = st.tabs(["👤 Profile", "🎨 Appearance", "ℹ️ Info"])

    # ─── TAB 1: PROFILE (EDIT MODE) ───
    with tab_profile:
        st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1, 2.5, 1])
        with c2:
            st.markdown(
                """
                <div style="margin-bottom: 16px;">
                    <div style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary);">Profile Information</div>
                    <div style="font-size: 0.82rem; color: var(--text-secondary);">Edit your details and avatar</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Avatar Display & Uploader
            avatar_html = get_avatar_html(user, "large")
            st.markdown(
                f"""
                <div style="display: flex; justify-content: center; margin-bottom: 12px;">
                    {avatar_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

            uploaded_file = st.file_uploader(
                "📷 Change Photo (PNG/JPG, max 2MB)",
                type=["png", "jpg", "jpeg"],
                key="avatar_upload",
            )

            profile_b64 = user.get("profile_image_b64")
            if uploaded_file is not None:
                if uploaded_file.size > 2 * 1024 * 1024:
                    st.error("❌ Image must be under 2MB")
                else:
                    bytes_data = uploaded_file.read()
                    profile_b64 = base64.b64encode(bytes_data).decode("utf-8")
                    st.success("✅ New avatar loaded! Click 'Save Changes' below.")

            st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)

            # Form Fields
            c_fn, c_ln = st.columns([1, 1])
            with c_fn:
                first_name_input = st.text_input("First Name", value=user.get("first_name", ""))
            with c_ln:
                last_name_input = st.text_input("Last Name", value=user.get("last_name", ""))

            st.text_input("Username", value=user.get("username", ""), disabled=True, help="Read-only")
            st.text_input("Email", value=user.get("email", ""), disabled=True, help="Read-only")
            phone_input = st.text_input("Phone Number", value=user.get("phone") or "")
            
            # Role Selection Dropdown (Student / Researcher)
            roles_list = ["Student", "Researcher"]
            current_role = user.get("role", "Student")
            role_idx = roles_list.index(current_role) if current_role in roles_list else 0
            role_input = st.selectbox("Role", options=roles_list, index=role_idx, help="Select account role (Student or Researcher)")

            st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)

            if st.button("💾 Save Changes", type="primary", use_container_width=True, key="btn_save_profile"):
                try:
                    updated = update_user_profile(
                        username=user["username"],
                        first_name=first_name_input,
                        last_name=last_name_input,
                        phone=phone_input,
                        profile_image_b64=profile_b64,
                        role=role_input,
                    )
                    st.session_state["user"] = updated
                    st.success("✅ Profile updated successfully!")
                    st.rerun()
                except ValueError as ve:
                    st.error(f"⚠️ {ve}")
                except Exception as ex:
                    st.error(f"❌ Failed to update profile. Try again. ({ex})")

    # ─── TAB 2: APPEARANCE (THEME) ───
    with tab_appearance:
        st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1, 2.5, 1])
        with c2:
            st.markdown(
                """
                <div style="margin-bottom: 16px;">
                    <div style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary);">Theme Preferences</div>
                    <div style="font-size: 0.82rem; color: var(--text-secondary);">Customize your visual experience</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            current_theme = st.session_state.get("theme", user.get("theme", "dark"))
            if "temp_theme" not in st.session_state:
                st.session_state["temp_theme"] = current_theme

            temp_theme = st.session_state.get("temp_theme", current_theme)

            # Theme Selection Cards
            col_dark, col_light = st.columns([1, 1])

            with col_dark:
                is_dark_selected = temp_theme == "dark"
                border_style = "2px solid #3b82f6" if is_dark_selected else "1px solid var(--border)"
                bg_style = "rgba(59, 130, 246, 0.1)" if is_dark_selected else "var(--bg-card)"
                
                st.markdown(
                    f"""
                    <div style="
                        border: {border_style};
                        background: {bg_style};
                        border-radius: 12px;
                        padding: 16px;
                        text-align: center;
                        margin-bottom: 10px;
                    ">
                        <div style="font-size: 2rem; margin-bottom: 6px;">🌙</div>
                        <div style="font-weight: 700; color: #e2e8f0; font-size: 0.95rem;">Dark Mode</div>
                        <div style="font-size: 0.75rem; color: #94a3b8;">{"[✓] Active" if is_dark_selected else "Sleek dark theme"}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Select Dark", key="select_dark_btn", use_container_width=True):
                    st.session_state["temp_theme"] = "dark"
                    st.rerun()

            with col_light:
                is_light_selected = temp_theme == "light"
                border_style = "2px solid #3b82f6" if is_light_selected else "1px solid var(--border)"
                bg_style = "rgba(59, 130, 246, 0.1)" if is_light_selected else "var(--bg-card)"

                st.markdown(
                    f"""
                    <div style="
                        border: {border_style};
                        background: {bg_style};
                        border-radius: 12px;
                        padding: 16px;
                        text-align: center;
                        margin-bottom: 10px;
                    ">
                        <div style="font-size: 2rem; margin-bottom: 6px;">☀️</div>
                        <div style="font-weight: 700; color: #0f172a; font-size: 0.95rem;">Light Mode</div>
                        <div style="font-size: 0.75rem; color: #64748b;">{"[✓] Active" if is_light_selected else "High contrast light"}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Select Light", key="select_light_btn", use_container_width=True):
                    st.session_state["temp_theme"] = "light"
                    st.rerun()

            st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)

            # Theme Live Preview Card
            preview_bg = "#111318" if temp_theme == "dark" else "#ffffff"
            preview_border = "#1e212b" if temp_theme == "dark" else "#cbd5e1"
            preview_text = "#e2e8f0" if temp_theme == "dark" else "#0f172a"
            preview_sub = "#94a3b8" if temp_theme == "dark" else "#64748b"

            st.markdown(
                f"""
                <div style="
                    background: {preview_bg};
                    border: 1px solid {preview_border};
                    border-radius: 12px;
                    padding: 16px;
                    margin-bottom: 20px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                ">
                    <div style="font-size: 0.8rem; font-weight: 600; color: {preview_sub}; margin-bottom: 6px;">LIVE THEME PREVIEW</div>
                    <div style="font-size: 1rem; font-weight: 700; color: {preview_text}; margin-bottom: 4px;">🎓 EKIP AI Workspace</div>
                    <div style="font-size: 0.82rem; color: {preview_sub};">Sample dashboard card preview for {temp_theme.upper()} mode.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Apply Button
            if st.button("Apply Theme", type="primary", use_container_width=True, key="btn_apply_theme_action"):
                theme_to_apply = st.session_state.get("temp_theme", "dark")
                update_user_theme(user["username"], theme_to_apply)
                st.session_state["theme"] = theme_to_apply
                st.session_state["user"] = get_user_by_username(user["username"])
                st.success("✅ Theme applied! Refreshing...")
                st.rerun()

    # ─── TAB 3: INFORMATION (ABOUT EKIP) ───
    with tab_info:
        st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns([0.1, 3.8, 0.1])
        with c2:
            # Header
            st.markdown(
                """
                <div style="text-align: center; margin-bottom: 24px; padding: 24px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 14px;">
                    <div style="font-size: 2.2rem; margin-bottom: 6px;">ℹ️</div>
                    <div style="font-size: 1.5rem; font-weight: 800; color: var(--text-primary); margin-bottom: 4px;">About EKIP</div>
                    <div style="font-size: 0.95rem; font-weight: 600; color: #3b82f6; margin-bottom: 10px;">Educational Knowledge Intelligence Platform</div>
                    <div style="font-size: 0.88rem; color: var(--text-secondary); max-width: 720px; margin: 0 auto; line-height: 1.6;">
                        EKIP is an AI-powered educational knowledge platform designed to help students and researchers discover, retrieve, understand, verify, and learn from trusted knowledge sources and uploaded documents.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # What is EKIP?
            st.markdown(
                """
                <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                    <div style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 8px;">🎓 What is EKIP?</div>
                    <div style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.6;">
                        EKIP (Educational Knowledge Intelligence Platform) is an AI-powered learning and knowledge system that combines document retrieval, trusted knowledge sources, verification, and AI-powered synthesis to help users learn from their educational materials.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Core Capabilities
            st.markdown('<div style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 12px;">🌟 Core Capabilities</div>', unsafe_allow_html=True)
            
            cap_col1, cap_col2 = st.columns([1, 1])
            with cap_col1:
                st.markdown(
                    """
                    <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 14px; margin-bottom: 12px;">
                        <div style="font-weight: 700; color: var(--text-primary); font-size: 0.9rem; margin-bottom: 4px;">💬 AI Knowledge Chat</div>
                        <div style="font-size: 0.82rem; color: var(--text-secondary);">Ask questions and receive grounded answers through the EKIP knowledge pipeline.</div>
                    </div>
                    <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 14px; margin-bottom: 12px;">
                        <div style="font-weight: 700; color: var(--text-primary); font-size: 0.9rem; margin-bottom: 4px;">📚 Document Intelligence</div>
                        <div style="font-size: 0.82rem; color: var(--text-secondary);">Upload and retrieve information from educational documents.</div>
                    </div>
                    <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 14px; margin-bottom: 12px;">
                        <div style="font-weight: 700; color: var(--text-primary); font-size: 0.9rem; margin-bottom: 4px;">🔎 Multi-Source Retrieval</div>
                        <div style="font-size: 0.82rem; color: var(--text-secondary);">Retrieve relevant knowledge from indexed sources and documents.</div>
                    </div>
                    <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 14px; margin-bottom: 12px;">
                        <div style="font-weight: 700; color: var(--text-primary); font-size: 0.9rem; margin-bottom: 4px;">🧠 Knowledge Synthesis</div>
                        <div style="font-size: 0.82rem; color: var(--text-secondary);">Combine retrieved evidence into a useful learning response.</div>
                    </div>
                    <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 14px; margin-bottom: 12px;">
                        <div style="font-weight: 700; color: var(--text-primary); font-size: 0.9rem; margin-bottom: 4px;">📝 Document Summarization</div>
                        <div style="font-size: 0.82rem; color: var(--text-secondary);">Generate summaries from uploaded study material.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with cap_col2:
                st.markdown(
                    """
                    <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 14px; margin-bottom: 12px;">
                        <div style="font-weight: 700; color: var(--text-primary); font-size: 0.9rem; margin-bottom: 4px;">⚖️ Topic Comparison</div>
                        <div style="font-size: 0.82rem; color: var(--text-secondary);">Compare educational concepts using retrieved knowledge.</div>
                    </div>
                    <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 14px; margin-bottom: 12px;">
                        <div style="font-weight: 700; color: var(--text-primary); font-size: 0.9rem; margin-bottom: 4px;">🧪 Practice Quiz</div>
                        <div style="font-size: 0.82rem; color: var(--text-secondary);">Generate document-grounded multiple-choice practice questions.</div>
                    </div>
                    <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 14px; margin-bottom: 12px;">
                        <div style="font-weight: 700; color: var(--text-primary); font-size: 0.9rem; margin-bottom: 4px;">📑 Study Notes</div>
                        <div style="font-size: 0.82rem; color: var(--text-secondary);">Generate structured study material from educational content.</div>
                    </div>
                    <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 14px; margin-bottom: 12px;">
                        <div style="font-weight: 700; color: var(--text-primary); font-size: 0.9rem; margin-bottom: 4px;">🔬 Research Discovery</div>
                        <div style="font-size: 0.82rem; color: var(--text-secondary);">Find educational/research sources where supported by the existing system.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)

            # EKIP Knowledge Pipeline
            st.markdown(
                """
                <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                    <div style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 14px; text-align: center;">🔄 EKIP Knowledge Pipeline</div>
                    <div style="display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap; gap: 8px;">
                        <div style="background: rgba(59, 130, 246, 0.12); border: 1px solid rgba(59, 130, 246, 0.3); padding: 8px 14px; border-radius: 20px; font-size: 0.82rem; color: #3b82f6; font-weight: 600;">❓ Ask</div>
                        <div style="color: var(--text-secondary); font-weight: 700;">➔</div>
                        <div style="background: rgba(139, 92, 246, 0.12); border: 1px solid rgba(139, 92, 246, 0.3); padding: 8px 14px; border-radius: 20px; font-size: 0.82rem; color: #8b5cf6; font-weight: 600;">🔎 Retrieve</div>
                        <div style="color: var(--text-secondary); font-weight: 700;">➔</div>
                        <div style="background: rgba(236, 72, 153, 0.12); border: 1px solid rgba(236, 72, 153, 0.3); padding: 8px 14px; border-radius: 20px; font-size: 0.82rem; color: #ec4899; font-weight: 600;">📚 Gather Sources</div>
                        <div style="color: var(--text-secondary); font-weight: 700;">➔</div>
                        <div style="background: rgba(34, 197, 94, 0.12); border: 1px solid rgba(34, 197, 94, 0.3); padding: 8px 14px; border-radius: 20px; font-size: 0.82rem; color: #22c55e; font-weight: 600;">✅ Verify</div>
                        <div style="color: var(--text-secondary); font-weight: 700;">➔</div>
                        <div style="background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.3); padding: 8px 14px; border-radius: 20px; font-size: 0.82rem; color: #f59e0b; font-weight: 600;">🧠 Synthesize</div>
                        <div style="color: var(--text-secondary); font-weight: 700;">➔</div>
                        <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.3); padding: 8px 14px; border-radius: 20px; font-size: 0.82rem; color: #10b981; font-weight: 600;">🎓 Learn</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Platform Architecture
            st.markdown(
                """
                <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                    <div style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 12px;">⚙️ Platform Architecture</div>
                    <ul style="color: var(--text-secondary); font-size: 0.85rem; line-height: 1.8; margin-left: -10px; margin-bottom: 0;">
                        <li><b>Streamlit UI:</b> Responsive dark-mode web application shell with dynamic tab navigation.</li>
                        <li><b>Python Backend:</b> LangGraph stateful planning engine with PyDantic models and Loguru observability.</li>
                        <li><b>Vector & Keyword Search:</b> Hybrid retrieval combining ChromaDB vector embeddings and BM25 text ranker.</li>
                        <li><b>Document Processing:</b> Automated PDF, DOCX, and TXT parsing, metadata extraction, and chunking.</li>
                        <li><b>Multi-Agent Orchestration:</b> Autonomous orchestrator managing intent routing, retrieval, verification, and synthesis agents.</li>
                        <li><b>Multi-LLM Synthesis:</b> Multi-provider routing supporting Gemini, Groq, Cohere, and Mistral models.</li>
                        <li><b>Auth & Session Storage:</b> SQLite database (<code>ekip_users.db</code>) with BCrypt hashing and token persistence.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Security & Authentication
            st.markdown(
                """
                <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                    <div style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 12px;">🔐 Security & Authentication</div>
                    <div style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.7;">
                        • <b>BCrypt Hashing:</b> Passwords are stored securely using salted BCrypt password hashing ($2b$).<br/>
                        • <b>TLS 1.3 Encryption:</b> Transport-layer security for user data and API communication.<br/>
                        • <b>Remember Me Tokens:</b> Secure UUID-based session tokens stored in SQLite with auto-invalidation.<br/>
                        • <b>Password Security:</b> Strict complexity validation for registration and password resets.<br/>
                        • <b>Role Management:</b> Controlled role validation (Student & Researcher) with database integrity constraints.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # User Roles
            st.markdown(
                """
                <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                    <div style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 12px;">👥 User Roles</div>
                    <div style="display: flex; gap: 16px; flex-wrap: wrap;">
                        <div style="flex: 1; min-width: 240px; background: rgba(59, 130, 246, 0.06); border: 1px solid rgba(59, 130, 246, 0.25); border-radius: 10px; padding: 14px;">
                            <div style="font-weight: 700; color: #3b82f6; font-size: 0.95rem; margin-bottom: 6px;">🎓 Student</div>
                            <div style="font-size: 0.82rem; color: var(--text-secondary); line-height: 1.5;">Designed for learners. Provides access to interactive AI chat, practice quizzes, study note generation, document Q&A, and guided learning paths.</div>
                        </div>
                        <div style="flex: 1; min-width: 240px; background: rgba(139, 92, 246, 0.06); border: 1px solid rgba(139, 92, 246, 0.25); border-radius: 10px; padding: 14px;">
                            <div style="font-weight: 700; color: #8b5cf6; font-size: 0.95rem; margin-bottom: 6px;">🔬 Researcher</div>
                            <div style="font-size: 0.82rem; color: var(--text-secondary); line-height: 1.5;">Designed for academic research. Enables multi-source knowledge retrieval, academic paper discovery, evidence verification, and in-depth topic comparison.</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Application Modules
            st.markdown('<div style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 12px;">🧩 Application Modules</div>', unsafe_allow_html=True)
            
            mod_col1, mod_col2 = st.columns([1, 1])
            with mod_col1:
                st.markdown(
                    """
                    <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 12px; margin-bottom: 10px;">
                        <div style="font-weight: 700; color: var(--text-primary); font-size: 0.88rem; margin-bottom: 2px;">💬 Chat</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary);">Conversational AI knowledge companion with source citations and agent trace.</div>
                    </div>
                    <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 12px; margin-bottom: 10px;">
                        <div style="font-weight: 700; color: var(--text-primary); font-size: 0.88rem; margin-bottom: 2px;">🎓 Student Workspace</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary);">Interactive learning suite with quizzes, study notes, summarization, and comparison tools.</div>
                    </div>
                    <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 12px; margin-bottom: 10px;">
                        <div style="font-weight: 700; color: var(--text-primary); font-size: 0.88rem; margin-bottom: 2px;">📊 Analytics</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary);">Query metrics, LLM performance telemetry, and system usage dashboard.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with mod_col2:
                st.markdown(
                    """
                    <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 12px; margin-bottom: 10px;">
                        <div style="font-weight: 700; color: var(--text-primary); font-size: 0.88rem; margin-bottom: 2px;">📁 Documents</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary);">Upload, manage, parse, and index educational reference documents.</div>
                    </div>
                    <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 12px; margin-bottom: 10px;">
                        <div style="font-weight: 700; color: var(--text-primary); font-size: 0.88rem; margin-bottom: 2px;">🩺 LLM Health & Diagnostics</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary);">Multi-provider model availability, latency monitoring, and subsystem diagnostics.</div>
                    </div>
                    <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 12px; margin-bottom: 10px;">
                        <div style="font-weight: 700; color: var(--text-primary); font-size: 0.88rem; margin-bottom: 2px;">⚙️ Settings</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary);">User profile management, theme customization, and platform information.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)

            # Version / System Info
            st.markdown(
                """
                <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 16px; text-align: center; margin-bottom: 24px;">
                    <div style="font-weight: 700; color: var(--text-primary); font-size: 0.95rem; margin-bottom: 6px;">🚀 EKIP Platform</div>
                    <div style="font-size: 0.82rem; color: var(--text-secondary); display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
                        <span><b>Version:</b> v2.5</span>
                        <span><b>Environment:</b> Production</span>
                        <span><b>Status:</b> <span style="color: #22c55e; font-weight: 600;">🟢 Operational</span></span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

