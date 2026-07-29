"""Centralized CSS Theme for Enterprise Multi-Agent RAG."""

def inject_theme() -> str:
    return """
    <style>
    /* Dark Theme Core */
    .stApp {
        background-color: #0e1117;
        color: #e6edf3;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #21262d;
    }

    /* Chat Messages */
    .stChatMessage {
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.6rem 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transition: all 0.2s ease-in-out;
    }
    .stChatMessage.user {
        background-color: #16243b;
        border: 1px solid #1f3a60;
    }
    .stChatMessage.assistant {
        background-color: #161b22;
        border-left: 4px solid #4cc9f0;
        border-top: 1px solid #30363d;
        border-right: 1px solid #30363d;
        border-bottom: 1px solid #30363d;
    }

    /* Source Cards & Boxes */
    .source-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 0.9rem;
        margin: 0.5rem 0;
        transition: border-color 0.2s ease;
    }
    .source-card:hover {
        border-color: #4cc9f0;
    }

    .agent-trace-box {
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
        font-size: 0.85rem;
        background-color: #0d1117;
        border: 1px solid #21262d;
        border-radius: 8px;
        padding: 0.8rem;
        color: #7ee787;
    }

    /* Buttons */
    div.stButton > button {
        background-color: #4cc9f0;
        color: #0d1117;
        font-weight: 600;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        transition: transform 0.15s ease, background-color 0.15s ease;
    }
    div.stButton > button:hover {
        background-color: #38b6ff;
        transform: translateY(-1px);
        color: #000;
    }
    div.stButton > button:active {
        transform: translateY(0);
    }

    /* Sidebar Navigation buttons */
    .conv-btn {
        text-align: left;
        border: none;
        background: transparent;
        color: #c9d1d9;
        padding: 0.6rem 0.8rem;
        width: 100%;
        border-radius: 8px;
        font-size: 0.9rem;
        cursor: pointer;
        transition: background-color 0.2s ease;
    }
    .conv-btn:hover {
        background-color: #21262d;
        color: #58a6ff;
    }
    .conv-active {
        background-color: #1f2937;
        color: #4cc9f0;
        font-weight: bold;
        border-left: 3px solid #4cc9f0;
    }

    /* Badges & Pills */
    .crag-pill {
        display: inline-block;
        background: #1e3a5f;
        color: #4cc9f0;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-left: 8px;
        border: 1px solid #4cc9f0;
    }

    .confidence-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .confidence-high { background-color: #0e3a1e; color: #3fb950; border: 1px solid #238636; }
    .confidence-medium { background-color: #3a2e0e; color: #d29922; border: 1px solid #9e6a03; }
    .confidence-low { background-color: #3a0e0e; color: #f85149; border: 1px solid #da3633; }

    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0d1117;
    }
    ::-webkit-scrollbar-thumb {
        background: #30363d;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #484f58;
    }
    </style>
    """
