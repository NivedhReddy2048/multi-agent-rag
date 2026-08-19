"""Document Knowledge Agent wrapping existing Vector DB & BM25 Hybrid Retrieval Engine."""

import time
from typing import List, Optional
from agents.sources.base_agent import BaseKnowledgeAgent
from core.models.domain import KnowledgeResult, SourceType
from core.logger import get_logger

logger = get_logger("agents.sources.document_agent")


class DocumentKnowledgeAgent(BaseKnowledgeAgent):
    """Retrieves uploaded internal document chunks via hybrid vector DB + BM25 retrieval."""

    def __init__(self, engine = None):
        super().__init__(
            agent_name="DocumentKnowledgeAgent",
            source_type=SourceType.INTERNAL_DOCUMENT,
            provider_key="uploaded_documents"
        )
        self.engine = engine

    def initialize(self) -> bool:
        if self.engine is None:
            try:
                from core.engine import BaseRAGEngine
                from config import Config
                self.engine = BaseRAGEngine.get_instance() or BaseRAGEngine(Config)
            except Exception as e:
                logger.warning(f"Could not initialize BaseRAGEngine in DocumentKnowledgeAgent: {e}")
        self.is_initialized = True
        logger.info("DocumentKnowledgeAgent initialized")
        return True

    def health(self) -> bool:
        return self.engine is not None

    def execute(self, query: str, max_results: int = 5, target_documents: Optional[List[str]] = None) -> List[KnowledgeResult]:
        if not self.is_initialized or self.engine is None:
            self.initialize()

        t0 = time.time()
        results: List[KnowledgeResult] = []

        try:
            if target_documents:
                doc_chunks = self.engine.hybrid_search(query, k=max_results, doc_filter=target_documents)
            else:
                total_docs = len(self.engine.list_docs()) if hasattr(self.engine, "list_docs") else 1
                k_per = max(2, max_results // max(1, total_docs))
                doc_chunks = self.engine.multi_doc_search(query, target_docs=None, k_per_doc=k_per)
                if not doc_chunks:
                    doc_chunks = self.engine.hybrid_search(query, k=max_results)

            lat = (time.time() - t0) * 1000

            for doc in doc_chunks:
                content = doc.page_content if hasattr(doc, "page_content") else str(doc)
                meta = doc.metadata if hasattr(doc, "metadata") else {}
                source_file = meta.get("source_file", meta.get("filename", meta.get("document_id", "Internal Document")))
                score = meta.get("rerank_score", meta.get("score", 0.85))

                results.append(KnowledgeResult(
                    provider="uploaded_documents",
                    source_type=SourceType.INTERNAL_DOCUMENT,
                    title=f"Doc: {source_file}",
                    content=content,
                    summary=content[:200] + "..." if len(content) > 200 else content,
                    confidence=float(score),
                    latency_ms=lat,
                    metadata=meta,
                ))
            logger.info(f"DocumentKnowledgeAgent retrieved {len(results)} doc chunks in {int(lat)}ms for target_docs={target_documents}")
        except Exception as e:
            logger.error(f"DocumentKnowledgeAgent error: {e}", exc_info=True)

        return results

