"""Database storage and session management for EKIP Chat System."""

import os
import json
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_DIR = PROJECT_ROOT / "data"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "ekip_chats.db"


def get_chat_db_path(custom_path: Optional[str] = None) -> Path:
    """Resolve SQLite database path for chats."""
    path = Path(custom_path) if custom_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


_initialized_dbs = set()


def _ensure_schema(conn: sqlite3.Connection):
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    pinned INTEGER DEFAULT 0,
                    message_count INTEGER DEFAULT 0,
                    first_message_preview TEXT
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    citations TEXT,
                    agent_trace TEXT,
                    confidence INTEGER,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
                );
                """
            )
            try:
                cur = conn.cursor()
                cur.execute("PRAGMA table_info(chat_messages)")
                existing_cols = {row[1] for row in cur.fetchall()}
                for col_name, col_type in [("citations", "TEXT"), ("agent_trace", "TEXT"), ("confidence", "INTEGER"), ("metadata", "TEXT")]:
                    if col_name not in existing_cols:
                        conn.execute(f"ALTER TABLE chat_messages ADD COLUMN {col_name} {col_type}")
            except Exception:
                pass
    except Exception:
        pass


def get_chat_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Get SQLite database connection with Row factory."""
    path = get_chat_db_path(db_path)
    str_path = str(path)
    conn = sqlite3.connect(str_path)
    conn.row_factory = sqlite3.Row
    if str_path not in _initialized_dbs:
        _initialized_dbs.add(str_path)
        _ensure_schema(conn)
    return conn


def init_chat_db(db_path: Optional[str] = None) -> str:
    """Initialize chat database tables if missing."""
    path = get_chat_db_path(db_path)
    conn = get_chat_db_connection(str(path))
    _ensure_schema(conn)
    conn.close()
    return str(path)
    return str(path)


def create_chat_session(
    user_id: str,
    title: str = "New Chat",
    first_message: str = "",
    db_path: Optional[str] = None,
) -> str:
    """Create a new chat session and return unique session_id."""
    session_id = str(uuid.uuid4())
    conn = get_chat_db_connection(db_path)
    preview = first_message[:100] if first_message else ""
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO chat_sessions (id, user_id, title, first_message_preview)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, user_id.strip(), title.strip() or "New Chat", preview),
            )
    finally:
        conn.close()
    return session_id


def get_chat_sessions(user_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all chat sessions for user ordered by pinned DESC, updated_at DESC."""
    if not user_id:
        return []
    conn = get_chat_db_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM chat_sessions
            WHERE LOWER(user_id) = LOWER(?)
            ORDER BY pinned DESC, updated_at DESC
            """,
            (user_id.strip(),),
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_chat_session(session_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve a single chat session by session_id."""
    if not session_id:
        return None
    conn = get_chat_db_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_chat_title(
    session_id: str, new_title: str, db_path: Optional[str] = None
) -> bool:
    """Update title for a chat session."""
    if not session_id or not new_title:
        return False
    conn = get_chat_db_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE chat_sessions
                SET title = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (new_title.strip(), session_id),
            )
            return cur.rowcount > 0
    finally:
        conn.close()


def toggle_pin_chat(session_id: str, db_path: Optional[str] = None) -> bool:
    """Toggle pinned status for a chat session."""
    if not session_id:
        return False
    conn = get_chat_db_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE chat_sessions
                SET pinned = CASE WHEN pinned = 1 THEN 0 ELSE 1 END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (session_id,),
            )
            return cur.rowcount > 0
    finally:
        conn.close()


def delete_chat_session(session_id: str, db_path: Optional[str] = None) -> bool:
    """Delete a chat session and associated messages."""
    if not session_id:
        return False
    conn = get_chat_db_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
            cur.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
            return cur.rowcount > 0
    finally:
        conn.close()


def increment_message_count(session_id: str, db_path: Optional[str] = None) -> bool:
    """Increment message count and update updated_at timestamp."""
    if not session_id:
        return False
    conn = get_chat_db_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE chat_sessions
                SET message_count = message_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (session_id,),
            )
            return cur.rowcount > 0
    finally:
        conn.close()


def update_chat_preview(
    session_id: str, preview: str, db_path: Optional[str] = None
) -> bool:
    """Update first message preview snippet for a chat session."""
    if not session_id:
        return False
    conn = get_chat_db_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE chat_sessions
                SET first_message_preview = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (preview[:100], session_id),
            )
            return cur.rowcount > 0
    finally:
        conn.close()


def save_message(
    session_id: Optional[str] = None,
    role: str = "user",
    content: str = "",
    citations: Optional[List[Dict[str, Any]]] = None,
    agent_trace: Optional[List[str]] = None,
    confidence: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
    **kwargs,
) -> bool:
    """Insert a single message into chat_messages table with rich metadata."""
    sid = session_id or kwargs.get("chat_id") or kwargs.get("conversation_id")
    r = role or kwargs.get("role", "user")
    c = content or kwargs.get("content", "")
    cits = citations if citations is not None else kwargs.get("citations")
    trace = agent_trace if agent_trace is not None else kwargs.get("agent_trace")
    conf = confidence if confidence is not None else kwargs.get("confidence")
    meta = metadata if metadata is not None else kwargs.get("metadata")
    path = db_path or kwargs.get("db_path")

    if not sid or not r or not c:
        return False
    conn = get_chat_db_connection(path)
    cits_json = json.dumps(cits) if cits else None
    trace_json = json.dumps(trace) if trace else None
    meta_json = json.dumps(meta) if meta else None
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO chat_messages (session_id, role, content, citations, agent_trace, confidence, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (sid, r, c, cits_json, trace_json, conf, meta_json),
            )
            return cur.rowcount > 0
    finally:
        conn.close()


def get_chat_messages(
    session_id: Optional[str] = None,
    limit: int = 1000,
    db_path: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """Retrieve all messages for a session ordered by id/timestamp ASC with deserialized metadata."""
    sid = session_id or kwargs.get("chat_id") or kwargs.get("conversation_id")
    lim = limit or kwargs.get("limit", 1000)
    path = db_path or kwargs.get("db_path")

    if not sid:
        return []
    conn = get_chat_db_connection(path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, session_id, role, content, timestamp, citations, agent_trace, confidence, metadata
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (sid, lim),
        )
        rows = cur.fetchall()
        result = []
        for r in rows:
            msg_dict = {
                "id": r["id"],
                "session_id": r["session_id"],
                "role": r["role"],
                "content": r["content"],
                "timestamp": r["timestamp"],
                "confidence": r["confidence"],
            }
            if r["citations"]:
                try:
                    cits = json.loads(r["citations"])
                    msg_dict["citations"] = cits
                    msg_dict["sources"] = cits
                except Exception:
                    pass
            if r["agent_trace"]:
                try:
                    msg_dict["agent_trace"] = json.loads(r["agent_trace"])
                except Exception:
                    pass
            if r["metadata"]:
                try:
                    msg_dict["metadata"] = json.loads(r["metadata"])
                except Exception:
                    pass
            result.append(msg_dict)
        return result
    finally:
        conn.close()


def get_message_count(session_id: str, db_path: Optional[str] = None) -> int:
    """Return total message count for a session."""
    if not session_id:
        return 0
    conn = get_chat_db_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) as cnt FROM chat_messages WHERE session_id = ?",
            (session_id,),
        )
        row = cur.fetchone()
        return row["cnt"] if row else 0
    finally:
        conn.close()


def delete_chat_messages(session_id: str, db_path: Optional[str] = None) -> bool:
    """Delete all messages for a given session."""
    if not session_id:
        return False
    conn = get_chat_db_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
            return cur.rowcount > 0
    finally:
        conn.close()
