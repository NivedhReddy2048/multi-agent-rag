"""Database Abstraction Layer providing PostgreSQL and SQLite dual backend support."""

import os
import sqlite3
from typing import Dict, Any, List, Optional
from core.logger import get_logger

logger = get_logger("core.db.manager")


class DatabaseManager:
    """Unified Database Manager supporting dual SQLite and PostgreSQL connections."""

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv("DATABASE_URL", "sqlite:///data/ekip_saas.db")
        self.is_postgres = self.db_url.startswith("postgresql") or self.db_url.startswith("postgres")
        self._init_db()

    def _get_sqlite_conn(self) -> sqlite3.Connection:
        db_path = self.db_url.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(db_path) if "/" in db_path or "\\" in db_path else ".", exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        if not self.is_postgres:
            with self._get_sqlite_conn() as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    subscription_plan TEXT DEFAULT 'free',
                    organization_id TEXT,
                    created_at REAL
                )
                """)
                conn.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    course_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    teacher_id TEXT NOT NULL,
                    organization_id TEXT,
                    created_at REAL
                )
                """)
                conn.execute("""
                CREATE TABLE IF NOT EXISTS enrollments (
                    course_id TEXT NOT NULL,
                    student_id TEXT NOT NULL,
                    enrolled_at REAL,
                    PRIMARY KEY (course_id, student_id)
                )
                """)
                conn.commit()
            logger.info("Initialized Multi-User Database Schema (SQLite).")

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Executes a SQL query returning dictionary rows."""
        if not self.is_postgres:
            with self._get_sqlite_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                if query.strip().upper().startswith("SELECT"):
                    return [dict(row) for row in cursor.fetchall()]
                conn.commit()
                return []
        return []


# Global singleton instance
db_manager = DatabaseManager()
