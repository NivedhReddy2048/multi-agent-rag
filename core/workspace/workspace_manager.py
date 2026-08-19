"""Student Workspace Manager handling persistent sessions, notebooks, bookmarks, collections, search & progress."""

import os
import json
import sqlite3
import uuid
import time
from typing import List, Dict, Any, Optional

from core.models.workspace import (
    LearningSession,
    Notebook,
    StudyNote,
    StudyCollection,
    Bookmark,
    WorkspaceProgress,
)
from core.logger import get_logger

logger = get_logger("core.workspace.manager")


class WorkspaceManager:
    """Manages student learning sessions, notebooks, library bookmarks, collections, search & progress."""

    def __init__(self, db_path: str = "workspace.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize SQLite tables for student workspace."""
        with self._get_conn() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS learning_sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                topics TEXT DEFAULT '[]',
                query_count INTEGER DEFAULT 0,
                created_at REAL,
                updated_at REAL
            );
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS notebooks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_at REAL
            );
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS study_notes (
                id TEXT PRIMARY KEY,
                session_id TEXT DEFAULT '',
                notebook_id TEXT DEFAULT '',
                query TEXT NOT NULL,
                title TEXT NOT NULL,
                ai_explanation TEXT DEFAULT '',
                key_takeaways TEXT DEFAULT '[]',
                important_terms TEXT DEFAULT '{}',
                created_at REAL
            );
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS study_collections (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                items TEXT DEFAULT '[]',
                created_at REAL
            );
            """)

            conn.execute("""
            CREATE TABLE IF NOT EXISTS bookmarks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                resource_type TEXT DEFAULT 'article',
                url TEXT DEFAULT '',
                is_read INTEGER DEFAULT 0,
                created_at REAL,
                metadata TEXT DEFAULT '{}'
            );
            """)
            conn.commit()
            logger.info("Initialized Workspace SQLite database tables successfully.")

    # --- Learning Sessions ---
    def create_session(self, title: str, description: str = "", topics: Optional[List[str]] = None) -> LearningSession:
        sid = str(uuid.uuid4())[:8]
        now = time.time()
        topics_json = json.dumps(topics or [])
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO learning_sessions (id, title, description, topics, query_count, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (sid, title, description, topics_json, 0, now, now),
            )
            conn.commit()
        return LearningSession(id=sid, title=title, description=description, topics=topics or [], query_count=0, created_at=now, updated_at=now)

    def list_sessions(self) -> List[LearningSession]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM learning_sessions ORDER BY updated_at DESC").fetchall()
            return [
                LearningSession(
                    id=r["id"],
                    title=r["title"],
                    description=r["description"],
                    topics=json.loads(r["topics"] or "[]"),
                    query_count=r["query_count"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    # --- Notebooks ---
    def create_notebook(self, title: str, description: str = "") -> Notebook:
        nid = str(uuid.uuid4())[:8]
        now = time.time()
        with self._get_conn() as conn:
            conn.execute("INSERT INTO notebooks (id, title, description, created_at) VALUES (?, ?, ?, ?)", (nid, title, description, now))
            conn.commit()
        return Notebook(id=nid, title=title, description=description, notes=[], created_at=now)

    def list_notebooks(self) -> List[Notebook]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM notebooks ORDER BY created_at DESC").fetchall()
            notebooks = []
            for r in rows:
                notes = self.get_notes_for_notebook(r["id"])
                notebooks.append(Notebook(id=r["id"], title=r["title"], description=r["description"], notes=notes, created_at=r["created_at"]))
            return notebooks

    # --- Study Notes ---
    def save_study_note(
        self,
        query: str,
        title: str,
        ai_explanation: str,
        session_id: str = "",
        notebook_id: str = "",
        key_takeaways: Optional[List[str]] = None,
        important_terms: Optional[Dict[str, str]] = None,
    ) -> StudyNote:
        nid = str(uuid.uuid4())[:8]
        now = time.time()
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO study_notes (id, session_id, notebook_id, query, title, ai_explanation, key_takeaways, important_terms, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (nid, session_id, notebook_id, query, title, ai_explanation, json.dumps(key_takeaways or []), json.dumps(important_terms or {}), now),
            )
            conn.commit()
        return StudyNote(
            id=nid,
            session_id=session_id,
            notebook_id=notebook_id,
            query=query,
            title=title,
            ai_explanation=ai_explanation,
            key_takeaways=key_takeaways or [],
            important_terms=important_terms or {},
            created_at=now,
        )

    def get_notes_for_notebook(self, notebook_id: str) -> List[StudyNote]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM study_notes WHERE notebook_id = ? ORDER BY created_at DESC", (notebook_id,)).fetchall()
            return [
                StudyNote(
                    id=r["id"],
                    session_id=r["session_id"],
                    notebook_id=r["notebook_id"],
                    query=r["query"],
                    title=r["title"],
                    ai_explanation=r["ai_explanation"],
                    key_takeaways=json.loads(r["key_takeaways"] or "[]"),
                    important_terms=json.loads(r["important_terms"] or "{}"),
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    # --- Bookmarks ---
    def add_bookmark(self, title: str, resource_type: str, url: str = "", metadata: Optional[Dict[str, Any]] = None) -> Bookmark:
        bid = str(uuid.uuid4())[:8]
        now = time.time()
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO bookmarks (id, title, resource_type, url, is_read, created_at, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (bid, title, resource_type, url, 0, now, json.dumps(metadata or {})),
            )
            conn.commit()
        return Bookmark(id=bid, title=title, resource_type=resource_type, url=url, is_read=False, created_at=now, metadata=metadata or {})

    def list_bookmarks(self) -> List[Bookmark]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM bookmarks ORDER BY created_at DESC").fetchall()
            return [
                Bookmark(
                    id=r["id"],
                    title=r["title"],
                    resource_type=r["resource_type"],
                    url=r["url"],
                    is_read=bool(r["is_read"]),
                    created_at=r["created_at"],
                    metadata=json.loads(r["metadata"] or "{}"),
                )
                for r in rows
            ]

    def toggle_bookmark_read(self, bookmark_id: str):
        with self._get_conn() as conn:
            conn.execute("UPDATE bookmarks SET is_read = CASE WHEN is_read = 1 THEN 0 ELSE 1 END WHERE id = ?", (bookmark_id,))
            conn.commit()

    # --- Study Collections ---
    def create_collection(self, title: str, category: str = "general", items: Optional[List[Dict[str, Any]]] = None) -> StudyCollection:
        cid = str(uuid.uuid4())[:8]
        now = time.time()
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO study_collections (id, title, category, items, created_at) VALUES (?, ?, ?, ?, ?)",
                (cid, title, category, json.dumps(items or []), now),
            )
            conn.commit()
        return StudyCollection(id=cid, title=title, category=category, items=items or [], created_at=now)

    def list_collections(self) -> List[StudyCollection]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM study_collections ORDER BY created_at DESC").fetchall()
            return [
                StudyCollection(
                    id=r["id"],
                    title=r["title"],
                    category=r["category"],
                    items=json.loads(r["items"] or "[]"),
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    # --- Smart Local Search ---
    def smart_search(self, search_query: str) -> Dict[str, List[Any]]:
        q_lower = search_query.lower()
        results = {"notes": [], "notebooks": [], "bookmarks": [], "collections": []}

        with self._get_conn() as conn:
            # Search Study Notes
            note_rows = conn.execute("SELECT * FROM study_notes WHERE LOWER(query) LIKE ? OR LOWER(title) LIKE ? OR LOWER(ai_explanation) LIKE ?", (f"%{q_lower}%", f"%{q_lower}%", f"%{q_lower}%")).fetchall()
            results["notes"] = [{"id": r["id"], "title": r["title"], "query": r["query"]} for r in note_rows]

            # Search Notebooks
            nb_rows = conn.execute("SELECT * FROM notebooks WHERE LOWER(title) LIKE ? OR LOWER(description) LIKE ?", (f"%{q_lower}%", f"%{q_lower}%")).fetchall()
            results["notebooks"] = [{"id": r["id"], "title": r["title"], "description": r["description"]} for r in nb_rows]

            # Search Bookmarks
            bm_rows = conn.execute("SELECT * FROM bookmarks WHERE LOWER(title) LIKE ? OR LOWER(url) LIKE ?", (f"%{q_lower}%", f"%{q_lower}%")).fetchall()
            results["bookmarks"] = [{"id": r["id"], "title": r["title"], "url": r["url"]} for r in bm_rows]

            # Search Collections
            col_rows = conn.execute("SELECT * FROM study_collections WHERE LOWER(title) LIKE ? OR LOWER(category) LIKE ?", (f"%{q_lower}%", f"%{q_lower}%")).fetchall()
            results["collections"] = [{"id": r["id"], "title": r["title"], "category": r["category"]} for r in col_rows]

        return results

    # --- Progress Dashboard Metrics ---
    def get_progress(self) -> WorkspaceProgress:
        with self._get_conn() as conn:
            sess_cnt = conn.execute("SELECT COUNT(*) FROM learning_sessions").fetchone()[0]
            notes_cnt = conn.execute("SELECT COUNT(*) FROM study_notes").fetchone()[0]
            nb_cnt = conn.execute("SELECT COUNT(*) FROM notebooks").fetchone()[0]
            bm_cnt = conn.execute("SELECT COUNT(*) FROM bookmarks").fetchone()[0]
            read_bm_cnt = conn.execute("SELECT COUNT(*) FROM bookmarks WHERE is_read = 1").fetchone()[0]
            col_cnt = conn.execute("SELECT COUNT(*) FROM study_collections").fetchone()[0]

            return WorkspaceProgress(
                total_queries=notes_cnt,
                total_sessions=sess_cnt,
                saved_notes_count=notes_cnt,
                notebooks_count=nb_cnt,
                bookmarks_count=bm_cnt,
                read_bookmarks_count=read_bm_cnt,
                collections_count=col_cnt,
                topics_explored=["Artificial Intelligence", "Neural Networks", "RAG Systems"],
            )


# Global singleton instance
workspace_manager = WorkspaceManager()
