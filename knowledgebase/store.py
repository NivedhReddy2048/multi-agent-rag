"""EKIP Vector & Metadata Storage Module.

Changes made:
- Encapsulated ChromaDB vector store initialization, persistent registry, and metadata query routines.
- Added structured Loguru logging for database operations.
"""

from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from core.logger import get_logger

logger = get_logger("knowledgebase.store")


class KnowledgeStore:
    """Enterprise Knowledge Store handling ChromaDB vectors and document registry."""

    def __init__(self, chroma_path: str, embeddings):
        self.chroma_path = chroma_path
        self.embeddings = embeddings
        self.vector_db = Chroma(
            persist_directory=chroma_path,
            embedding_function=embeddings,
        )
        logger.info(f"Initialized Persistent Knowledge Store at '{chroma_path}'")

    def add_chunks(self, chunks: List[Document], ids: List[str]):
        """Add document chunks to ChromaDB vector store."""
        try:
            self.vector_db.add_documents(chunks, ids=ids)
            logger.info(f"Added {len(chunks)} chunks to vector database.")
        except Exception as e:
            logger.error(f"Error adding chunks to ChromaDB: {e}")
            raise e

    def delete_chunks(self, ids: List[str]):
        """Delete chunks by IDs from ChromaDB vector store."""
        if not ids:
            return
        try:
            self.vector_db.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} chunks from vector database.")
        except Exception as e:
            logger.error(f"Error deleting chunks from ChromaDB: {e}")

    def similarity_search_with_scores(
        self, query: str, k: int = 8, doc_filter: Optional[List[str]] = None
    ) -> List[tuple[Document, float]]:
        """Perform dense similarity search with relevance scores."""
        filter_dict = None
        if doc_filter:
            valid = [f for f in doc_filter if f]
            if len(valid) == 1:
                filter_dict = {"document_id": valid[0]}
            elif len(valid) > 1:
                filter_dict = {"document_id": {"$in": valid}}

        try:
            results = self.vector_db.similarity_search_with_score(
                query, k=k, filter=filter_dict
            )
            return results
        except Exception as e:
            logger.warning(f"ChromaDB similarity search fallback without filter: {e}")
            return self.vector_db.similarity_search_with_score(query, k=k)
