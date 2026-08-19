"""Document metadata and management API layer for EKIP Platform."""

import os
import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from core.auth.database import get_db_connection


def init_documents_table(db_path: Optional[str] = None):
    """Initialize documents and document_chunks tables if missing."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    title TEXT NOT NULL,
                    type TEXT NOT NULL,
                    size_bytes INTEGER DEFAULT 0,
                    chunk_count INTEGER DEFAULT 0,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'indexed'
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    page_number INTEGER DEFAULT 1,
                    char_count INTEGER DEFAULT 0,
                    metadata_json TEXT,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                );
                """
            )
    finally:
        conn.close()


def save_user_document(
    user_id: str,
    filename: str,
    title: str,
    doc_type: str,
    size_bytes: int,
    chunks: List[Any],
    db_path: Optional[str] = None,
) -> str:
    """Save document metadata and chunks into SQLite database."""
    init_documents_table(db_path)
    doc_id = str(uuid.uuid4())
    conn = get_db_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO documents (id, user_id, filename, title, type, size_bytes, chunk_count, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'indexed')
                """,
                (doc_id, user_id.strip(), filename, title, doc_type, size_bytes, len(chunks)),
            )

            for idx, chk in enumerate(chunks):
                content = getattr(chk, "page_content", str(chk))
                meta = getattr(chk, "metadata", {}) if hasattr(chk, "metadata") else {}
                page = meta.get("page_number", meta.get("page", 1)) if isinstance(meta, dict) else 1
                cur.execute(
                    """
                    INSERT INTO document_chunks (document_id, chunk_index, text, page_number, char_count)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (doc_id, idx, content, page, len(content)),
                )
    finally:
        conn.close()
    return doc_id


def get_user_documents(user_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all documents uploaded by user with metadata."""
    init_documents_table(db_path)
    if not user_id:
        return []
    conn = get_db_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM documents
            WHERE LOWER(user_id) = LOWER(?)
            ORDER BY uploaded_at DESC
            """,
            (user_id.strip(),),
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_user_document(user_id: str, document_id: str, db_path: Optional[str] = None) -> bool:
    """Delete document and all associated chunks from database."""
    init_documents_table(db_path)
    if not document_id:
        return False
    conn = get_db_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM document_chunks WHERE document_id = ?", (document_id,))
            cur.execute(
                "DELETE FROM documents WHERE id = ? AND LOWER(user_id) = LOWER(?)",
                (document_id, user_id.strip()),
            )
            return cur.rowcount > 0
    finally:
        conn.close()


def get_document_chunks(document_id: str, limit: int = 50, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve text chunks for a given document for inspection."""
    init_documents_table(db_path)
    if not document_id:
        return []
    conn = get_db_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM document_chunks
            WHERE document_id = ?
            ORDER BY chunk_index ASC
            LIMIT ?
            """,
            (document_id, limit),
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def reindex_document(user_id: str, document_id: str, db_path: Optional[str] = None) -> bool:
    """Update document status to indexed."""
    init_documents_table(db_path)
    conn = get_db_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE documents SET status = 'indexed', uploaded_at = CURRENT_TIMESTAMP
                WHERE id = ? AND LOWER(user_id) = LOWER(?)
                """,
                (document_id, user_id.strip()),
            )
            return cur.rowcount > 0
    finally:
        conn.close()
