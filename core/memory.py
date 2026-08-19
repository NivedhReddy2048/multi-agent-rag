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
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional
from collections import Counter
from contextlib import contextmanager
from core.logger import get_logger

logger = get_logger("core.memory")


class ConversationMemory:
    """SQLite conversation memory, message persistence, and analytics logger."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        if db_path == ":memory:":
            self.db_path = f"file:memdb_{id(self)}?mode=memory&cache=shared"
            self._persistent_conn = sqlite3.connect(self.db_path, uri=True, check_same_thread=False)
            self._persistent_conn.row_factory = sqlite3.Row
        else:
            self._persistent_conn = None
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_conn(self):
        if self._persistent_conn is not None:
            yield self._persistent_conn
        else:
            conn = sqlite3.connect(self.db_path, timeout=20.0)
            conn.row_factory = sqlite3.Row
            try:
                conn.execute("PRAGMA journal_mode=WAL;")
            except Exception:
                pass
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def close(self):
        """Close active database connections cleanly."""
        if hasattr(self, "_persistent_conn") and self._persistent_conn is not None:
            try:
                self._persistent_conn.close()
            except Exception:
                pass
            self._persistent_conn = None


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
            # Phase 2 Educational Metrics & Memory Schema Extensions
            for col in [
                ("query_analytics", "knowledge_sources_used TEXT DEFAULT '[]'"),
                ("query_analytics", "learning_time REAL DEFAULT 0.0"),
                ("query_analytics", "research_queries INTEGER DEFAULT 0"),
                ("query_analytics", "book_queries INTEGER DEFAULT 0"),
                ("query_analytics", "video_queries INTEGER DEFAULT 0"),
                ("query_analytics", "recommended_questions_clicked INTEGER DEFAULT 0"),
                ("query_analytics", "planner_route TEXT DEFAULT ''"),
                ("query_analytics", "learning_session_id TEXT DEFAULT ''"),
                ("query_analytics", "planner_intent TEXT DEFAULT ''"),
                ("query_analytics", "planner_difficulty TEXT DEFAULT ''"),
                ("query_analytics", "planner_sources TEXT DEFAULT '[]'"),
                ("query_analytics", "planner_strategy TEXT DEFAULT ''"),
                ("query_analytics", "estimated_latency TEXT DEFAULT ''"),
                ("query_analytics", "estimated_cost TEXT DEFAULT ''"),
                ("query_analytics", "executed_sources TEXT DEFAULT '[]'"),
                ("query_analytics", "successful_sources TEXT DEFAULT '[]'"),
                ("query_analytics", "failed_sources TEXT DEFAULT '[]'"),
                ("query_analytics", "parallel_execution_time REAL DEFAULT 0.0"),
                ("query_analytics", "individual_latencies TEXT DEFAULT '{}'"),
                ("query_analytics", "provider_failures TEXT DEFAULT '[]'"),
                ("query_analytics", "verification_score REAL DEFAULT 0.0"),
                ("query_analytics", "agreement_score REAL DEFAULT 0.0"),
                ("query_analytics", "conflict_count INTEGER DEFAULT 0"),
                ("query_analytics", "duplicate_count INTEGER DEFAULT 0"),
                ("query_analytics", "ranking_latency REAL DEFAULT 0.0"),
                ("query_analytics", "verification_latency REAL DEFAULT 0.0"),
                ("query_analytics", "synthesis_latency REAL DEFAULT 0.0"),
                ("query_analytics", "educational_mode TEXT DEFAULT ''"),
                ("query_analytics", "guided_questions_generated INTEGER DEFAULT 0"),
                ("query_analytics", "learning_path_generated INTEGER DEFAULT 0"),
                ("query_analytics", "notebook_usage INTEGER DEFAULT 0"),
                ("query_analytics", "saved_responses INTEGER DEFAULT 0"),
                ("query_analytics", "bookmarks_count INTEGER DEFAULT 0"),
                ("query_analytics", "exports_count INTEGER DEFAULT 0"),
                ("query_analytics", "flashcards_generated INTEGER DEFAULT 0"),
                ("query_analytics", "quiz_attempts INTEGER DEFAULT 0"),
                ("query_analytics", "avg_quiz_score REAL DEFAULT 0.0"),
                ("query_analytics", "revision_usage INTEGER DEFAULT 0"),
                ("query_analytics", "interview_practice INTEGER DEFAULT 0"),
                ("query_analytics", "coding_exercises INTEGER DEFAULT 0"),
                ("query_analytics", "module_execution_latency REAL DEFAULT 0.0"),
                ("conversations", "learning_path TEXT DEFAULT ''"),




                ("conversations", "learning_level TEXT DEFAULT 'intermediate'"),
                ("conversations", "preferred_sources TEXT DEFAULT '[]'"),
            ]:
                try:
                    conn.execute(f"ALTER TABLE {col[0]} ADD COLUMN {col[1]}")
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

    def record_planner_telemetry(self, query: str, plan_data: Dict[str, Any]):
        """Record planner execution plan analytics into query_analytics table."""
        intent = str(plan_data.get("intent", ""))
        difficulty = str(plan_data.get("difficulty", ""))
        sources = json.dumps([str(s) for s in plan_data.get("selected_sources", [])])
        strategy = str(plan_data.get("retrieval_strategy", ""))
        est_latency = str(plan_data.get("estimated_latency", ""))
        est_cost = str(plan_data.get("estimated_cost", ""))

        with self._get_conn() as conn:
            conn.execute("""
            INSERT INTO query_analytics
            (query, intent, planner_intent, planner_difficulty, planner_sources, planner_strategy, estimated_latency, estimated_cost, source_mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (query, intent, intent, difficulty, sources, strategy, est_latency, est_cost, "planner_only"))
            conn.commit()
            logger.info(f"Recorded Planner Telemetry | Query: '{query[:30]}...' | Intent: {intent} | Difficulty: {difficulty}")

    def record_collection_telemetry(self, query: str, collection_data: Dict[str, Any]):
        """Record parallel knowledge collection telemetry into query_analytics table."""
        requested = json.dumps(collection_data.get("sources_requested", []))
        completed = json.dumps(collection_data.get("sources_completed", []))
        failed = json.dumps(collection_data.get("sources_failed", []))
        tot_lat = float(collection_data.get("total_latency_ms", 0.0))
        lat_map = json.dumps(collection_data.get("provider_latencies", {}))

        with self._get_conn() as conn:
            conn.execute("""
            INSERT INTO query_analytics
            (query, intent, executed_sources, successful_sources, failed_sources, parallel_execution_time, individual_latencies, provider_failures, source_mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (query, "knowledge_collection", requested, completed, failed, tot_lat, lat_map, failed, "parallel_collection"))
            conn.commit()
            logger.info(f"Recorded Collection Telemetry | Query: '{query[:30]}...' | Success: {completed} | Failed: {failed}")

    def record_verification_telemetry(self, query: str, ver_data: Dict[str, Any]):
        """Record knowledge verification analytics into query_analytics table."""
        ver_score = float(ver_data.get("overall_confidence", 0.0))
        agr_score = float(ver_data.get("overall_agreement", 0.0))
        conflict_count = len(ver_data.get("conflicts", []))
        duplicate_count = len(ver_data.get("duplicates", []))
        ver_latency = float(ver_data.get("total_latency_ms", 0.0))

        with self._get_conn() as conn:
            conn.execute("""
            INSERT INTO query_analytics
            (query, intent, verification_score, agreement_score, conflict_count, duplicate_count, verification_latency, source_mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (query, "knowledge_verification", ver_score, agr_score, conflict_count, duplicate_count, ver_latency, "knowledge_verification"))
            conn.commit()
            logger.info(f"Recorded Verification Telemetry | Query: '{query[:30]}...' | VerScore: {ver_score} | AgrScore: {agr_score} | Conflicts: {conflict_count}")

    def record_synthesis_telemetry(self, query: str, edu_data: Dict[str, Any]):
        """Record educational response synthesis analytics into query_analytics table."""
        mode = str(edu_data.get("educational_mode", "detailed_explanation"))
        guided_count = len(edu_data.get("guided_questions", []))
        has_lpath = 1 if edu_data.get("learning_path") else 0
        syn_meta = edu_data.get("synthesis_metadata", {})
        syn_latency = float(syn_meta.get("composer_latency_ms", 0.0)) + float(syn_meta.get("synthesis_latency_ms", 0.0))

        with self._get_conn() as conn:
            conn.execute("""
            INSERT INTO query_analytics
            (query, intent, educational_mode, guided_questions_generated, learning_path_generated, synthesis_latency, source_mode)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (query, "educational_synthesis", mode, guided_count, has_lpath, syn_latency, "educational_synthesis"))
            conn.commit()
            logger.info(f"Recorded Synthesis Telemetry | Query: '{query[:30]}...' | Mode: {mode} | GuidedQs: {guided_count}")

    def record_workspace_telemetry(self, query: str, action: str, details: Dict[str, Any]):
        """Record student workspace user interactions into query_analytics table."""
        with self._get_conn() as conn:
            conn.execute("""
            INSERT INTO query_analytics
            (query, intent, educational_mode, notebook_usage, saved_responses, bookmarks_count, exports_count, source_mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (query, f"workspace_{action}", action, details.get("notebook_usage", 0), details.get("saved_responses", 0), details.get("bookmarks_count", 0), details.get("exports_count", 0), "workspace_interaction"))
            conn.commit()
            logger.info(f"Recorded Workspace Telemetry | Query: '{query[:30]}...' | Action: {action}")

    def record_module_telemetry(self, query: str, module_name: str, metrics: Dict[str, Any]):
        """Record Learning Module execution analytics into query_analytics table."""
        with self._get_conn() as conn:
            conn.execute("""
            INSERT INTO query_analytics
            (query, intent, educational_mode, flashcards_generated, quiz_attempts, avg_quiz_score, revision_usage, interview_practice, coding_exercises, module_execution_latency, source_mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query,
                f"module_{module_name.lower()}",
                module_name,
                metrics.get("flashcards_generated", 0),
                metrics.get("quiz_attempts", 0),
                float(metrics.get("avg_quiz_score", 0.0)),
                metrics.get("revision_usage", 0),
                metrics.get("interview_practice", 0),
                metrics.get("coding_exercises", 0),
                float(metrics.get("module_execution_latency", 0.0)),
                "learning_module",
            ))
            conn.commit()
            logger.info(f"Recorded Module Telemetry | Query: '{query[:30]}...' | Module: {module_name}")






