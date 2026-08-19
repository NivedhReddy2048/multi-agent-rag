"""Centralized Enterprise Dark CSS Theme for EKIP Platform."""


def inject_theme(theme=None) -> str:
    """Inject CSS theme variables. Returns a <style> HTML string."""
    import streamlit as st

    if theme is None:
        theme = st.session_state.get("theme", "dark")

    themes = {
        "dark": {
            "--bg-primary": "#0b0d12",
            "--bg-secondary": "#111318",
            "--bg-card": "#111318",
            "--border": "#1e212b",
            "--text-primary": "#e2e8f0",
            "--text-secondary": "#94a3b8",
            "--accent": "#ef4444",
            "--accent-hover": "#dc2626",
            "--input-bg": "#0b0d12",
            "--input-border": "#1e212b",
            "--input-focus": "#3b82f6",
            "--success": "#22c55e",
            "--warning": "#f59e0b",
        },
        "light": {
            "--bg-primary": "#f8fafc",
            "--bg-secondary": "#ffffff",
            "--bg-card": "#ffffff",
            "--border": "#e2e8f0",
            "--text-primary": "#0f172a",
            "--text-secondary": "#64748b",
            "--accent": "#ef4444",
            "--accent-hover": "#dc2626",
            "--input-bg": "#f1f5f9",
            "--input-border": "#cbd5e1",
            "--input-focus": "#3b82f6",
            "--success": "#16a34a",
            "--warning": "#d97706",
        },
    }

    selected = themes.get(theme, themes["dark"])
    root_vars_lines = "\n".join([f"        {k}: {v};" for k, v in selected.items()])
    root_vars = f":root {{\n{root_vars_lines}\n    }}"

    base_css = """
    /* ─── Typography & Core Colors ─── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: system-ui, -apple-system, 'Inter', sans-serif !important;
        font-size: 13px !important;
        color: var(--text-secondary) !important;
    }

    .stApp {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }

    /* Hide standard Streamlit header chrome, menu, footer */
    #MainMenu, footer, header, [data-testid="stHeader"], [data-testid="stDecoration"] {
        visibility: hidden !important;
        height: 0px !important;
        margin: 0px !important;
        padding: 0px !important;
    }

    .main .block-container {
        padding-top: 0rem !important;
        padding-bottom: 2rem !important;
        max-width: 1100px !important;
    }

    /* ─── Top Navigation Bar ─── */
    .top-nav-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: 56px;
        padding: 0 24px;
        border-bottom: 1px solid #1e212b;
        background: rgba(11, 13, 18, 0.95);
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }

    /* ─── ANIMATED MESH GRADIENT & COVER PAGE STYLES ─── */
    @keyframes meshGradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    @keyframes logoPulse {
        0%, 100% { transform: scale(1); filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.4)); }
        50% { transform: scale(1.08); filter: drop-shadow(0 0 18px rgba(239, 68, 68, 0.75)); }
    }

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(24px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .cover-cta-primary button, button[kind="primary"] {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 14px rgba(239, 68, 68, 0.3) !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }

    .cover-cta-primary button:hover, button[kind="primary"]:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 0 24px rgba(239, 68, 68, 0.5) !important;
        background: linear-gradient(135deg, #f87171 0%, #ef4444 100%) !important;
    }

    /* ─── ANIMATED BACKGROUND ORBS, DOT GRID & NOISE LAYER ─── */
    .orb-1 {
        position: fixed; width: 600px; height: 600px; border-radius: 50%;
        background: radial-gradient(circle, rgba(59,130,246,0.10) 0%, transparent 70%);
        top: -200px; left: -200px; filter: blur(80px); pointer-events: none; z-index: 0;
        animation: float1 20s ease-in-out infinite;
    }
    .orb-2 {
        position: fixed; width: 500px; height: 500px; border-radius: 50%;
        background: radial-gradient(circle, rgba(139,92,246,0.08) 0%, transparent 70%);
        bottom: -150px; right: -150px; filter: blur(80px); pointer-events: none; z-index: 0;
        animation: float2 25s ease-in-out infinite;
    }
    .orb-3 {
        position: fixed; width: 400px; height: 400px; border-radius: 50%;
        background: radial-gradient(circle, rgba(236,72,153,0.05) 0%, transparent 70%);
        top: 40%; right: 5%; filter: blur(80px); pointer-events: none; z-index: 0;
        animation: float3 18s ease-in-out infinite;
    }
    @keyframes float1 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(30px,20px)} }
    @keyframes float2 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-20px,-30px)} }
    @keyframes float3 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(15px,-15px)} }

    .dot-grid {
        position: fixed; inset: 0;
        background-image: radial-gradient(rgba(255,255,255,0.035) 1px, transparent 1px);
        background-size: 32px 32px;
        pointer-events: none; z-index: 0;
    }

    .noise {
        position: fixed; inset: 0; opacity: 0.025; pointer-events: none; z-index: 0;
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
    }

    /* ─── LOGIN PAGE SINGLE-CARD CENTERED VIEWPORT (NO SCROLL) ─── */
    .login-wrapper {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: #0b0d12 !important;
        z-index: 99999 !important;
        overflow: hidden !important;
    }

    .login-card-inner {
        width: 100% !important;
        max-width: 420px !important;
        position: relative !important;
        z-index: 10 !important;
    }

    .login-card-inner [data-testid="stForm"] {
        width: 100% !important;
        background: #111318 !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 16px !important;
        padding: 36px 40px !important;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5) !important;
        position: relative !important;
        overflow: hidden !important;
        z-index: 10 !important;
    }

    .login-card-inner [data-testid="stForm"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        opacity: 0.6;
    }

    .login-logo-circle {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: linear-gradient(135deg, #ec4899, #8b5cf6);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin: 0 auto 16px auto;
        box-shadow: 0 4px 16px rgba(139, 92, 246, 0.3);
    }

    .login-app-title {
        font-size: 20px;
        font-weight: 600;
        color: #e8e9ec;
        text-align: center;
        margin-bottom: 6px;
    }

    .login-app-sub {
        font-size: 14px;
        color: #9ca3af;
        text-align: center;
        margin-bottom: 24px;
    }

    .input-field-label {
        font-size: 12px;
        font-weight: 500;
        color: #9ca3af;
        margin-bottom: 6px;
        display: block;
    }

    .forgot-pass-link {
        text-align: right;
    }

    .forgot-pass-link a, .forgot-pass-link span {
        color: #3b82f6;
        font-size: 12px;
        text-decoration: none;
        cursor: pointer;
    }

    .forgot-pass-link a:hover, .forgot-pass-link span:hover {
        text-decoration: underline;
    }

    .login-card-footer {
        font-size: 11px;
        color: #4b5563;
        text-align: center;
        margin-top: 24px;
        padding-top: 16px;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
    }

    /* ─── Global Streamlit Button Overrides ─── */
    div.stButton > button {
        background-color: #181b21 !important;
        border: 1px solid rgba(255, 255, 255, 0.10) !important;
        color: #e8e9ec !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        padding: 0.4rem 0.8rem !important;
        transition: all 0.15s ease !important;
    }

    div.stButton > button:hover {
        background-color: #1e222a !important;
        border-color: rgba(255, 255, 255, 0.15) !important;
        color: #ffffff !important;
        transform: translateY(-1px) !important;
    }

    div.stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
        border: none !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        height: 44px !important;
        font-size: 14px !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3) !important;
    }

    div.stButton > button[data-testid="baseButton-primary"]:hover {
        filter: brightness(1.1) !important;
        transform: translateY(-1px) !important;
    }

    /* ─── Input Field Overrides & Password Visibility ─── */
    /* Fix dark password inputs on dark background - single outer border */
    div[data-baseweb="input"],
    div[data-baseweb="input"] > div {
        background-color: #0b0d12 !important;
        border: 1px solid #1e212b !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
        min-height: 42px !important;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        display: flex !important;
        align-items: center !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }

    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="input"] > div:focus-within {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    }

    input[type="password"],
    input[type="text"] {
        background-color: transparent !important;
        color: #e2e8f0 !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        padding: 10px 14px !important;
        font-size: 0.9rem !important;
        width: 100% !important;
    }

    input[type="password"]:focus,
    input[type="text"]:focus {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }

    /* Ensure placeholder text is visible */
    input::placeholder {
        color: #475569 !important;
    }

    /* Hide browser default password reveal buttons */
    input::-ms-reveal,
    input::-ms-clear,
    input::-webkit-contacts-auto-fill-button,
    input::-webkit-credentials-auto-fill-button {
        display: none !important;
        width: 0px !important;
        height: 0px !important;
    }

    div[data-testid="stTextInput"] {
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    }

    div[data-baseweb="input"] input {
        color: #e2e8f0 !important;
        font-size: 0.9rem !important;
        padding: 10px 14px !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        outline: none !important;
    }

    div[data-baseweb="input"]:focus-within > div {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    }

    /* ─── Sidebar Styling ─── */
    [data-testid="stSidebar"] {
        background-color: #111318 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
        width: 280px !important;
    }

    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.4rem !important;
        padding-top: 0rem !important;
    }

    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 14px 12px 14px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        margin-bottom: 8px;
    }

    .sidebar-brand-logo {
        width: 32px;
        height: 32px;
        border-radius: 8px;
        background: linear-gradient(135deg, #ec4899, #8b5cf6);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        color: #ffffff;
        box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
    }

    .sidebar-brand-title {
        font-size: 15px;
        font-weight: 600;
        color: #e8e9ec;
        line-height: 1.1;
    }

    .sidebar-brand-sub {
        font-size: 11px;
        color: #6b7280;
        margin-top: 2px;
    }

    .sidebar-hdr {
        font-size: 10px;
        font-weight: 600;
        color: #4b5563;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 12px 10px 4px 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .sidebar-chat-item {
        font-size: 12px;
        color: #6b7280;
        padding: 6px 10px;
        border-radius: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: pointer;
        transition: background-color 0.15s ease;
    }

    .sidebar-chat-item:hover {
        background-color: #181b21;
        color: #e8e9ec;
    }

    .sidebar-footer-info {
        font-size: 11px;
        color: #4b5563;
        padding: 8px 10px 0 10px;
    }

    /* ─── Main Header Bar ─── */
    .top-main-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: 56px;
        background: #0b0d10;
        backdrop-filter: blur(8px);
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        padding: 0 20px;
        margin-bottom: 20px;
    }

    .header-breadcrumb {
        font-size: 13px;
        color: #6b7280;
    }

    .header-breadcrumb span {
        color: #e8e9ec;
        font-weight: 500;
    }

    .header-right {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .header-avatar {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: 700;
        color: #ffffff;
    }

    /* ─── Hero Card ─── */
    .hero-card {
        background: linear-gradient(135deg, rgba(59,130,246,0.06), rgba(139,92,246,0.03));
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 28px 32px;
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
    }

    .hero-card-glow {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        opacity: 0.6;
    }

    .hero-meta-row {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 14px;
    }

    .hero-meta-pill {
        background: #181b21;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 6px;
        padding: 3px 10px;
        font-size: 11px;
        color: #9ca3af;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    .hero-lbl {
        font-size: 10px;
        font-weight: 600;
        color: #4b5563;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .hero-title {
        font-size: 28px;
        font-weight: 700;
        color: #e8e9ec;
        letter-spacing: -0.02em;
        margin-bottom: 8px;
    }

    .hero-sub {
        font-size: 14px;
        color: #9ca3af;
        max-width: 640px;
        line-height: 1.5;
        margin-bottom: 16px;
    }

    .hero-pipeline-row {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
    }

    .hero-pipeline-step {
        background: #181b21;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 12px;
        color: #e8e9ec;
    }

    .hero-pipeline-arrow {
        color: #4b5563;
        font-size: 12px;
    }

    /* ─── Quick Start Action Cards ─── */
    .quick-start-lbl {
        font-size: 10px;
        font-weight: 600;
        color: #4b5563;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 12px;
    }

    .input-hint-text {
        text-align: center;
        font-size: 11px;
        color: #4b5563;
        margin-top: 8px;
    }

    /* ─── REMOVE MICROPHONE / VOICE BUTTON COMPLETELY ─── */
    button[title*="Microphone"],
    button[title*="voice"],
    button[aria-label*="Microphone"],
    button[aria-label*="voice"],
    button[title*="Speech"],
    button[title*="Audio"],
    div[data-testid="stChatInput"] button svg[data-icon="microphone"],
    div[data-testid="stChatInput"] button:has(svg path[d*="M12 14"]) {
        display: none !important;
        visibility: hidden !important;
        width: 0px !important;
        height: 0px !important;
    }

    div[data-testid="stChatInput"] {
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        background-color: #111318 !important;
    }

    div[data-testid="stChatInput"]:focus-within {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 1px #3b82f6 !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 5px;
        height: 5px;
    }
    ::-webkit-scrollbar-track {
        background: #0b0d12;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.2);
    }

    button[kind="secondary"][data-testid="baseButton-secondary"] {
        background: transparent !important;
        border: 1px solid #1e212b !important;
        color: #94a3b8 !important;
        border-radius: 6px !important;
        min-width: 32px !important;
        padding: 0px 8px !important;
    }
    button[kind="secondary"]:hover {
        border-color: #3b82f6 !important;
        color: #3b82f6 !important;
        background: #1a1d26 !important;
    }

    /* Sidebar Chat History Row & Action Buttons Styling */
    section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
        gap: 2px !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stColumn"] {
        padding: 0px 1px !important;
        min-width: 0px !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stColumn"] button {
        min-width: 0px !important;
        height: 34px !important;
        min-height: 34px !important;
        padding: 0px 2px !important;
        font-size: 0.82rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border-radius: 6px !important;
        border: 1px solid #1e212b !important;
        background: #111318 !important;
        color: #94a3b8 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stColumn"] button:hover {
        border-color: #3b82f6 !important;
        color: #3b82f6 !important;
        background: #1a1d26 !important;
    }

    /* Sidebar Enterprise Navigation Buttons Styling */
    section[data-testid="stSidebar"] button[key^="nav_item_"] {
        text-align: left !important;
        justify-content: flex-start !important;
        height: 38px !important;
        min-height: 38px !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        margin-bottom: 2px !important;
        padding-left: 12px !important;
        transition: all 0.15s ease !important;
    }

    section[data-testid="stSidebar"] button[key^="nav_item_"][kind="secondary"] {
        background: transparent !important;
        border: 1px solid transparent !important;
        color: #94a3b8 !important;
    }

    section[data-testid="stSidebar"] button[key^="nav_item_"][kind="secondary"]:hover {
        background: #161922 !important;
        color: #f1f5f9 !important;
        border-color: #1e212b !important;
    }

    section[data-testid="stSidebar"] button[key^="nav_item_"][kind="primary"] {
        background: rgba(59, 130, 246, 0.14) !important;
        border: 1px solid rgba(59, 130, 246, 0.4) !important;
        border-left: 3px solid #3b82f6 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1) !important;
    }

    /* Top-Right Profile Popover Button Styling */
    div[data-testid="stPopover"] button {
        background: #111318 !important;
        border: 1px solid #1e212b !important;
        color: #e2e8f0 !important;
        border-radius: 8px !important;
        height: 38px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        transition: all 0.15s ease !important;
    }

    div[data-testid="stPopover"] button:hover {
        border-color: #3b82f6 !important;
        color: #ffffff !important;
        background: #161922 !important;
    }

    /* Enterprise Quick Start Action Buttons Styling */
    div[data-testid="stColumn"] button[key^="qs_"] {
        background: #111318 !important;
        border: 1px solid #1e212b !important;
        border-radius: 10px !important;
        padding: 14px 16px !important;
        height: 72px !important;
        min-height: 72px !important;
        text-align: left !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: flex-start !important;
        justify-content: center !important;
        white-space: pre-wrap !important;
        color: #f8fafc !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        transition: all 0.15s ease-in-out !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15) !important;
    }

    div[data-testid="stColumn"] button[key^="qs_"]:hover {
        border-color: #3b82f6 !important;
        background: #161922 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 14px rgba(59, 130, 246, 0.12) !important;
    }

    div[data-testid="stColumn"] button[key^="qs_"] p {
        margin: 0 !important;
        line-height: 1.35 !important;
    }

    /* Hero Card & Knowledge Pipeline Styling */
    .hero-card {
        position: relative;
        background: #111318;
        border: 1px solid #1e212b;
        border-radius: 14px;
        padding: 26px 30px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }

    .hero-lbl {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: #3b82f6;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .hero-title {
        font-size: 1.65rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 10px;
        line-height: 1.25;
    }

    .hero-sub {
        font-size: 0.92rem;
        color: #94a3b8;
        line-height: 1.55;
        margin-bottom: 22px;
        max-width: 800px;
    }

    .hero-pipeline-container {
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
        padding-top: 16px;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
    }

    .hero-pipeline-item {
        display: flex;
        align-items: center;
        gap: 8px;
        background: #161922;
        border: 1px solid #1e212b;
        padding: 6px 14px;
        border-radius: 8px;
        font-size: 0.82rem;
        font-weight: 500;
        color: #e2e8f0;
    }

    .hero-pipeline-icon {
        font-size: 0.95rem;
    }

    .hero-pipeline-arrow {
        color: #3b82f6;
        font-weight: 600;
        font-size: 0.9rem;
    }
    """
    sidebar_toggle_css = get_sidebar_toggle_css()
    return "<style>\n" + root_vars + "\n" + base_css + "\n" + sidebar_toggle_css + "\n</style>"


def get_sidebar_toggle_css() -> str:
    """Returns CSS for animated sidebar collapse/expand toggle."""
    import streamlit as st

    collapsed = st.session_state.get("sidebar_collapsed", False)
    if collapsed:
        return """
        <style>
        section[data-testid="stSidebar"] {
            width: 0px !important; min-width: 0px !important; max-width: 0px !important;
            transform: translateX(-100%); transition: all 0.3s ease;
            overflow: hidden; visibility: hidden; padding: 0 !important; margin: 0 !important;
        }
        section[data-testid="stSidebar"] + section,
        .main .block-container {
            margin-left: 0px !important;
            width: 100% !important;
            max-width: 100% !important;
            transition: all 0.3s ease;
        }
        .sidebar-toggle-float { display: flex !important; }
        .sidebar-toggle-header { display: none !important; }
        button[kind="header"], [data-testid="stSidebarCollapseButton"] { display: none !important; }
        </style>
        """
    else:
        return """
        <style>
        section[data-testid="stSidebar"] {
            width: 260px !important; min-width: 260px !important;
            transform: translateX(0); transition: all 0.3s ease;
            visibility: visible;
        }
        section[data-testid="stSidebar"] + section {
            margin-left: 0px !important;
            transition: all 0.3s ease;
        }
        .sidebar-toggle-float { display: none !important; }
        .sidebar-toggle-header { display: flex !important; }
        button[kind="header"], [data-testid="stSidebarCollapseButton"] { display: none !important; }
        </style>
        """


def get_chart_colors(theme="dark"):
    """Returns theme-aware color dictionary for charts and analytics."""
    if theme == "dark":
        return {
            "primary": "#3b82f6",
            "secondary": "#8b5cf6",
            "accent": "#ef4444",
            "success": "#22c55e",
            "warning": "#f59e0b",
            "grid": "#1e212b",
            "text": "#e2e8f0",
            "subtext": "#94a3b8",
            "bg": "#0b0d12",
        }
    else:
        return {
            "primary": "#2563eb",
            "secondary": "#7c3aed",
            "accent": "#dc2626",
            "success": "#16a34a",
            "warning": "#d97706",
            "grid": "#e2e8f0",
            "text": "#0f172a",
            "subtext": "#64748b",
            "bg": "#ffffff",
        }
