"""Hybrid retrieval agent (Dense + Sparse + Rerank) for EKIP Platform.

Changes made:
- Added Loguru logging for search execution and candidate filtering.
- Ensured every retrieved chunk dictionary returned contains Document (source_file), Page (page), Chunk ID (chunk_id), and Similarity Score (score).
"""

import time
from typing import Dict, Any
from .base import BaseAgent, AgentResult
from core.logger import get_logger

logger = get_logger("agents.retrieval")


class RetrievalAgent(BaseAgent):
    """Hybrid Retrieval Agent performing Dense Search, BM25, RRF, and CrossEncoder Reranking."""

    name = "retrieval"
    description = "Dense + Sparse + Rerank hybrid retrieval agent"

    def __init__(self, engine):
        self.engine = engine

    def run(self, context: Dict[str, Any]) -> AgentResult:
        t0 = time.time()
        request_id = context.get("request_id", "")
        query = context["query"]
        doc_filter = context.get("doc_filter")
        filters = context.get("filters", {})
        top_k = context.get("top_k", 8)

        candidate_docs = None
        if doc_filter:
            candidate_docs = doc_filter if isinstance(doc_filter, list) else [doc_filter]

        logger.info(f"[{request_id}] RetrievalAgent searching for: '{query}' (doc_filter: {candidate_docs})")

        sub_latencies = {}

        # 1. Dense Search (ChromaDB)
        t_dense = time.time()
        dense = self.engine.dense_search(query, k=top_k, doc_filter=candidate_docs)
        sub_latencies["dense_retrieval_ms"] = round((time.time() - t_dense) * 1000, 2)
        logger.info(f"[{request_id}] STAGE dense_retrieval finished in {sub_latencies['dense_retrieval_ms']}ms")

        # 2. Sparse Search (BM25)
        t_sparse = time.time()
        sparse = self.engine.sparse_search(query, k=top_k)
        sub_latencies["sparse_retrieval_ms"] = round((time.time() - t_sparse) * 1000, 2)
        logger.info(f"[{request_id}] STAGE sparse_retrieval finished in {sub_latencies['sparse_retrieval_ms']}ms")

        if filters.get("source_file"):
            dense = [d for d in dense if d.metadata.get("source_file") == filters["source_file"]]
            sparse = [d for d in sparse if d.metadata.get("source_file") == filters["source_file"]]

        # 3. RRF Fusion
        t_rrf = time.time()
        fused = self.engine.reciprocal_rank_fusion(dense, sparse)
        sub_latencies["rrf_fusion_ms"] = round((time.time() - t_rrf) * 1000, 2)
        logger.info(f"[{request_id}] STAGE rrf_fusion finished in {sub_latencies['rrf_fusion_ms']}ms")

        # 4. CrossEncoder Rerank
        t_rerank = time.time()
        reranked = self.engine.rerank(query, fused, top_k=self.engine.cfg.RERANK_TOP_K)
        sub_latencies["cross_encoder_rerank_ms"] = round((time.time() - t_rerank) * 1000, 2)
        logger.info(f"[{request_id}] STAGE cross_encoder_rerank finished in {sub_latencies['cross_encoder_rerank_ms']}ms")

        compressed = self.engine.compress_context(reranked, max_chunks=6)

        latency = int((time.time() - t0) * 1000)
        confidence = self.engine.confidence()

        sources = []
        for d in compressed:
            sources.append({
                "content": d.page_content,
                "source_file": d.metadata.get("source_file", "Unknown"),
                "page": d.metadata.get("page_number", 1),
                "chunk_id": d.metadata.get("chunk_id", ""),
                "score": round(float(d.metadata.get("score", 0.0)), 4),
            })

        logger.info(f"[{request_id}] RetrievalAgent retrieved {len(sources)} chunks with confidence {confidence}% ({latency}ms)")

        return AgentResult(
            confidence=confidence,
            sources=sources,
            agent_trace=[f"Retrieved {len(sources)} chunks in {latency}ms"],
            metadata={
                "latency_ms": latency,
                "dense_hits": len(dense),
                "sparse_hits": len(sparse),
                "stage_latency_ms": sub_latencies,
                "source_mode": "documents" if sources else "none",
            }
        )
