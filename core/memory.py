"""SQLite-backed conversation memory & query analytics system for EKIP Platform.

Changes made:
- Added feedback column to messages table for user feedback persistence.
- Added tokens column to query_analytics table.
- Integrated Loguru logging across database operations.
- Added record_feedback method to update message feedback.
- Ensured thread-safe WAL mode and connection handling.
"""

import sqlite3
import json
import uuid
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from collections import Counter
from core.logger import get_logger

logger = get_logger("core.memory")


class ConversationMemory:
    """SQLite conversation memory, message persistence, and analytics logger."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=20.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                agent_trace TEXT,
                citations TEXT,
                confidence INTEGER,
                latency_ms INTEGER,
                feedback TEXT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS query_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                intent TEXT,
                confidence INTEGER,
                faithfulness REAL,
                blocked BOOLEAN,
                latency_ms INTEGER,
                keywords TEXT,
                agents_used TEXT,
                crag_used BOOLEAN DEFAULT 0,
                web_results_count INTEGER DEFAULT 0,
                tokens INTEGER DEFAULT 0,
                source_mode TEXT DEFAULT 'none',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS blocked_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                reason TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            # Safely check and add missing columns if upgrading database
            try:
                conn.execute("ALTER TABLE messages ADD COLUMN feedback TEXT DEFAULT NULL")
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE messages ADD COLUMN metadata TEXT DEFAULT NULL")
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE query_analytics ADD COLUMN tokens INTEGER DEFAULT 0")
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE query_analytics ADD COLUMN source_mode TEXT DEFAULT 'none'")
            except Exception:
                pass
            conn.commit()
            logger.info(f"Initialized SQLite database schema at '{self.db_path}'")

    def create_conversation(self, title: str = "New Chat") -> str:
        cid = str(uuid.uuid4())[:8]
        with self._get_conn() as conn:
            conn.execute("INSERT INTO conversations (id, title) VALUES (?, ?)", (cid, title))
            conn.commit()
            logger.info(f"Created new conversation session ID '{cid}' ('{title}')")
        return cid

    def list_conversations(self) -> List[Dict]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM conversations ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def add_message(
        self,
        conversation_id: Optional[str] = None,
        role: str = "user",
        content: str = "",
        confidence: Optional[int] = 0,
        citations: Optional[List[Dict]] = None,
        metadata: Optional[Dict] = None,
        timestamp: Optional[str] = None,
        agent_trace: Optional[List[str]] = None,
        latency_ms: int = 0,
        feedback: Optional[str] = None,
        conv_id: Optional[str] = None,
        **kwargs
    ):
        cid = conversation_id or conv_id or kwargs.get("conv_id", "")
        trace = agent_trace or kwargs.get("agent_trace", [])
        cits = citations or kwargs.get("citations", [])
        meta = metadata if metadata is not None else kwargs.get("metadata", {})
        if not isinstance(meta, dict):
            meta = {}
        meta.setdefault("source_mode", "none")
        conf = confidence if confidence is not None else 0
        lat = latency_ms or kwargs.get("latency_ms", 0)
        fb = feedback or kwargs.get("feedback", None)

        with self._get_conn() as conn:
            conn.execute("""
            INSERT INTO messages (conversation_id, role, content, agent_trace, citations, confidence, latency_ms, feedback, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cid, role, content,
                  json.dumps(trace or []),
                  json.dumps(cits or []),
                  conf, lat, fb,
                  json.dumps(meta or {})))
            conn.commit()
            logger.debug(f"Saved {role} message to conversation '{cid}'")

    def record_feedback(self, message_id: int, feedback: str):
        """Record user feedback (e.g. thumbs_up, thumbs_down, text) for a message."""
        with self._get_conn() as conn:
            conn.execute("UPDATE messages SET feedback = ? WHERE id = ?", (feedback, message_id))
            conn.commit()
            logger.info(f"Updated feedback for message ID {message_id}: '{feedback}'")

    def get_messages(self, conv_id: str) -> List[Dict]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at",
                (conv_id,)
            ).fetchall()
            result = []
            for r in rows:
                item = dict(r)
                try:
                    item['agent_trace'] = json.loads(item.get('agent_trace') or "[]")
                except Exception:
                    item['agent_trace'] = []
                try:
                    item['citations'] = json.loads(item.get('citations') or "[]")
                except Exception:
                    item['citations'] = []
                try:
                    item['metadata'] = json.loads(item.get('metadata') or "{}")
                except Exception:
                    item['metadata'] = {}
                result.append(item)
            return result

    def log_query_analytics(
        self,
        query: str,
        intent: str,
        confidence: int,
        faithfulness: float,
        blocked: bool,
        latency_ms: int,
        agent_trace: List[str],
        source_mode: str = "none",
        crag_used: bool = False,
        web_results_count: int = 0,
        tokens: int = 0,
    ):
        keywords = json.dumps(self._extract_keywords(query))
        agents = json.dumps(agent_trace)
        with self._get_conn() as conn:
            conn.execute("""
            INSERT INTO query_analytics
            (query, intent, confidence, faithfulness, blocked, latency_ms, keywords, agents_used, crag_used, web_results_count, tokens, source_mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (query, intent, confidence, faithfulness, blocked, latency_ms,
                  keywords, agents, crag_used, web_results_count, tokens, source_mode))
            if blocked:
                conn.execute(
                    "INSERT INTO blocked_queries (query, reason) VALUES (?, ?)",
                    (query, "Hallucination guard triggered")
                )
            conn.commit()
            logger.info(f"Logged query analytics | Query: '{query[:30]}...' | Intent: {intent} | Latency: {latency_ms}ms")

    def _extract_keywords(self, query: str) -> List[str]:
        words = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one',
            'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old',
            'see', 'two', 'who', 'boy', 'did', 'she', 'use', 'way', 'many', 'oil', 'sit', 'set', 'run',
            'eat', 'far', 'sea', 'eye', 'ago', 'off', 'too', 'any', 'say', 'man', 'try', 'ask', 'end',
            'why', 'let', 'put', 'own', 'tell', 'very', 'when', 'much', 'would', 'there', 'their',
            'what', 'said', 'each', 'which', 'will', 'about', 'could', 'other', 'after', 'first', 'never',
            'these', 'think', 'where', 'being', 'every', 'great', 'might', 'shall', 'still', 'those',
            'while', 'this', 'that', 'with', 'have', 'from', 'they', 'know', 'want', 'been', 'good',
            'some', 'time', 'come', 'here', 'just', 'like', 'long', 'make', 'over', 'such', 'take',
            'than', 'them', 'well', 'were', 'what', 'your', 'please', 'document', 'file', 'show', 'list'
        }
        return [w for w in words if w not in stop_words][:5]

    def get_total_queries(self) -> int:
        with self._get_conn() as conn:
            row = conn.execute("SELECT COUNT(*) FROM query_analytics").fetchone()
            return row[0] if row else 0

    def get_avg_confidence(self) -> float:
        with self._get_conn() as conn:
            row = conn.execute("SELECT AVG(confidence) FROM query_analytics").fetchone()
            return float(row[0]) if row and row[0] is not None else 0.0

    def get_blocked_count(self) -> int:
        with self._get_conn() as conn:
            row = conn.execute("SELECT COUNT(*) FROM blocked_queries").fetchone()
            return row[0] if row else 0

    def get_crag_trigger_count(self) -> int:
        with self._get_conn() as conn:
            row = conn.execute("SELECT COUNT(*) FROM query_analytics WHERE crag_used = 1").fetchone()
            return row[0] if row else 0

    def get_top_keywords(self, limit: int = 20) -> List[Tuple[str, int]]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT keywords FROM query_analytics").fetchall()
            all_words = []
            for row in rows:
                try:
                    all_words.extend(json.loads(row[0]))
                except Exception:
                    pass
            return Counter(all_words).most_common(limit)

    def get_agent_performance(self) -> List[Dict]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
            SELECT intent, AVG(latency_ms) as avg_latency_ms, COUNT(*) as count
            FROM query_analytics
            GROUP BY intent
            """).fetchall()
            return [dict(r) for r in rows]

    def get_faithfulness_distribution(self) -> List[float]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT faithfulness FROM query_analytics WHERE faithfulness IS NOT NULL").fetchall()
            return [r[0] for r in rows if r[0] is not None]

    def get_blocked_queries(self, limit: int = 50) -> List[Dict]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM blocked_queries ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_all_analytics(self) -> List[Dict]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM query_analytics ORDER BY timestamp DESC").fetchall()
            return [dict(r) for r in rows]
