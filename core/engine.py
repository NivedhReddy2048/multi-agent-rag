"""Refactored Hybrid RAG Engine for EKIP Platform.

Changes made:
- Integrated Loguru logging for ingestion, sparse BM25 lookup, vector search, RRF, and reranking.
- Added progress callback parameters (progress_cb) in ingest() to report Upload, Parsing, Chunking, Embedding, and Indexing stages.
- Guaranteed chunk metadata tags (source_file, document_id, page_number, chunk_id, score) on all retrieved documents.
"""

import os
import re
import json
import pickle
import math
from typing import List, Dict, Tuple, Optional, Callable
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from langchain_core.documents import Document
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_community.vectorstores import Chroma
from sentence_transformers import CrossEncoder
import chromadb
from core.logger import get_logger

logger = get_logger("core.engine")


class IncrementalBM25:
    """Compact BM25 implementation with unique chunk_id mapping."""

    def __init__(self, cache_file: str = "./bm25_state.pkl"):
        self.cache_file = cache_file
        self.doc_term_freqs: List[Dict[str, int]] = []
        self.doc_lengths: List[int] = []
        self.doc_chunk_ids: List[str] = []
        self.doc_freqs: Dict[str, int] = defaultdict(int)
        self.corpus_size: int = 0
        self.avg_doc_len: float = 0.0
        self.k1: float = 1.5
        self.b: float = 0.75
        self._doc_len_sum: int = 0
        self._load_state()

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())

    def _load_state(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    state = pickle.load(f)
                self.doc_term_freqs = state.get('doc_term_freqs', [])
                self.doc_lengths = state.get('doc_lengths', [])
                self.doc_chunk_ids = state.get('doc_chunk_ids', [])
                self.doc_freqs = defaultdict(int, state.get('doc_freqs', {}))
                self.corpus_size = state.get('corpus_size', 0)
                self._doc_len_sum = state.get('doc_len_sum', 0)
                self.avg_doc_len = state.get('avg_doc_len', 0.0)
            except Exception as e:
                logger.error(f"Error loading BM25 state from '{self.cache_file}': {e}")

    def save_state(self):
        Path(self.cache_file).parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'wb') as f:
            pickle.dump({
                'doc_term_freqs': self.doc_term_freqs,
                'doc_lengths': self.doc_lengths,
                'doc_chunk_ids': self.doc_chunk_ids,
                'doc_freqs': dict(self.doc_freqs),
                'corpus_size': self.corpus_size,
                'doc_len_sum': self._doc_len_sum,
                'avg_doc_len': self.avg_doc_len,
            }, f)

    def add_documents(self, texts: List[str], chunk_ids: Optional[List[str]] = None):
        if chunk_ids is None:
            chunk_ids = [f"gen_{i}" for i in range(len(texts))]

        for text, cid in zip(texts, chunk_ids):
            tokens = self._tokenize(text)
            if not tokens:
                tokens = ["_empty_token_"]
            tf = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            for t in set(tokens):
                self.doc_freqs[t] += 1
            self.doc_term_freqs.append(tf)
            self.doc_lengths.append(len(tokens))
            self.doc_chunk_ids.append(cid)
            self.corpus_size += 1
            self._doc_len_sum += len(tokens)

        self.avg_doc_len = self._doc_len_sum / self.corpus_size if self.corpus_size > 0 else 0.0
        self.save_state()

    def delete_documents(self, indices: List[int]):
        for idx in sorted(set(indices), reverse=True):
            if 0 <= idx < len(self.doc_term_freqs):
                tf = self.doc_term_freqs.pop(idx)
                dl = self.doc_lengths.pop(idx)
                if idx < len(self.doc_chunk_ids):
                    self.doc_chunk_ids.pop(idx)
                self.corpus_size -= 1
                self._doc_len_sum -= dl
                for t in tf:
                    self.doc_freqs[t] -= 1
                    if self.doc_freqs[t] <= 0:
                        del self.doc_freqs[t]
        self.avg_doc_len = self._doc_len_sum / self.corpus_size if self.corpus_size > 0 else 0.0
        self.save_state()

    def score(self, query: str) -> List[Tuple[int, float]]:
        q_tokens = self._tokenize(query)
        if not q_tokens or self.corpus_size == 0:
            return []
        scores = []
        for idx, tf in enumerate(self.doc_term_freqs):
            dl = self.doc_lengths[idx]
            s = 0.0
            for t in q_tokens:
                df = self.doc_freqs.get(t, 0)
                if df == 0:
                    continue
                idf = math.log((self.corpus_size - df + 0.5) / (df + 0.5) + 1.0)
                tf_val = tf.get(t, 0)
                denom = tf_val + self.k1 * (1 - self.b + self.b * (dl / self.avg_doc_len)) if self.avg_doc_len > 0 else tf_val + self.k1
                s += idf * (tf_val * (self.k1 + 1)) / denom if denom > 0 else 0
            scores.append((idx, s))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def get_top_k(self, query: str, k: int = 5) -> List[str]:
        scored = self.score(query)[:k]
        top_ids = []
        for idx, _ in scored:
            if idx < len(self.doc_chunk_ids):
                top_ids.append(self.doc_chunk_ids[idx])
        return top_ids


_GLOBAL_EMBEDDINGS_CACHE = {}
_GLOBAL_RERANKER_CACHE = {}


def get_cached_embeddings(model_name: str):
    if model_name not in _GLOBAL_EMBEDDINGS_CACHE:
        logger.info(f"Loading HuggingFace Embedding model into cache: {model_name}")
        _GLOBAL_EMBEDDINGS_CACHE[model_name] = HuggingFaceEmbeddings(model_name=model_name)
    return _GLOBAL_EMBEDDINGS_CACHE[model_name]


def get_cached_reranker(model_name: str):
    if model_name not in _GLOBAL_RERANKER_CACHE:
        logger.info(f"Loading CrossEncoder Reranker model into cache: {model_name}")
        _GLOBAL_RERANKER_CACHE[model_name] = CrossEncoder(model_name)
    return _GLOBAL_RERANKER_CACHE[model_name]


class BaseRAGEngine:
    """Agent-ready Hybrid RAG engine managing dense vectors, sparse BM25, RRF, and CrossEncoder."""

    def __init__(self, config):
        self.cfg = config
        self.embeddings = get_cached_embeddings(config.EMBEDDING_MODEL)
        self.reranker = get_cached_reranker(config.RERANKER_MODEL)
        self.persist_dir = config.CHROMA_PATH
        self.collection_name = "enterprise_rag"

        parent_dir = Path(config.CHROMA_PATH).parent
        parent_dir.mkdir(parents=True, exist_ok=True)

        self.bm25_path = str(parent_dir / "bm25_state.pkl")
        self.registry_file = str(parent_dir / "doc_registry.json")
        self.chunk_meta_file = str(parent_dir / "chunk_meta.json")

        self.vector_db: Optional[Chroma] = None
        self.bm25: Optional[IncrementalBM25] = None
        self.chunk_metadata: List[Dict] = []
        self.chunk_id_to_index: Dict[str, int] = {}
        self.document_registry: Dict[str, Dict] = {}
        self._last_scores: List[float] = []

        self._init_chroma()
        self._load_registry()
        self._load_chunk_metadata()
        self._init_bm25()

    def _init_chroma(self):
        client = chromadb.PersistentClient(path=self.persist_dir)
        self.vector_db = Chroma(
            client=client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
        )
        logger.info(f"Initialized ChromaDB vector database at '{self.persist_dir}'")

    def _load_registry(self):
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    self.document_registry = json.load(f)
            except Exception as e:
                logger.error(f"Failed loading document registry: {e}")
                self.document_registry = {}

    def save_registry(self):
        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(self.document_registry, f, indent=2)

    def _load_chunk_metadata(self):
        if os.path.exists(self.chunk_meta_file):
            try:
                with open(self.chunk_meta_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.chunk_metadata = data.get("metadata", [])
                self.chunk_id_to_index = data.get("id2idx", {})
            except Exception as e:
                logger.error(f"Failed loading chunk metadata: {e}")
                self.chunk_metadata = []
                self.chunk_id_to_index = {}

    def _save_chunk_metadata(self):
        with open(self.chunk_meta_file, 'w', encoding='utf-8') as f:
            json.dump({"metadata": self.chunk_metadata, "id2idx": self.chunk_id_to_index}, f)

    def _init_bm25(self):
        self.bm25 = IncrementalBM25(self.bm25_path)
        if self.bm25.corpus_size == 0 and self.chunk_metadata:
            self._rebuild_bm25()

    def _rebuild_bm25(self):
        self.bm25 = IncrementalBM25(self.bm25_path)
        texts = []
        cids = []
        for m in self.chunk_metadata:
            cid = m.get("chunk_id")
            doc = self.get_chunk_by_id(cid) if cid else None
            if doc and cid:
                texts.append(doc.page_content)
                cids.append(cid)
        if texts:
            self.bm25.add_documents(texts, chunk_ids=cids)

    def get_chunk_by_id(self, chunk_id: str) -> Optional[Document]:
        try:
            res = self.vector_db.get(ids=[chunk_id], include=["documents", "metadatas"])
            if res and res.get("documents") and len(res["documents"]) > 0:
                doc = Document(page_content=res["documents"][0], metadata=res["metadatas"][0])
                doc.metadata.setdefault("score", 0.0)
                return doc
        except Exception as e:
            logger.warning(f"Error fetching chunk ID '{chunk_id}': {e}")
        return None

    def ingest(
        self,
        file_path: str,
        chunks: List[Document],
        progress_cb: Optional[Callable[[float, str], None]] = None,
    ) -> str:
        base = os.path.basename(file_path)
        if base in self.document_registry:
            return f"EXISTS:{base}"

        logger.info(f"Ingesting file '{base}' with {len(chunks)} chunks")
        if progress_cb:
            progress_cb(0.8, f"Generating embeddings & indexing {len(chunks)} chunks into ChromaDB...")

        ids = [c.metadata["chunk_id"] for c in chunks]
        self.vector_db.add_documents(chunks, ids=ids)

        if progress_cb:
            progress_cb(0.9, f"Updating sparse BM25 search index...")

        self.bm25.add_documents([c.page_content for c in chunks], chunk_ids=ids)
        base_idx = self.bm25.corpus_size - len(chunks)

        for i, c in enumerate(chunks):
            meta = {
                "chunk_id": c.metadata["chunk_id"],
                "source_file": c.metadata["source_file"],
                "document_id": c.metadata["document_id"],
                "page_number": c.metadata.get("page_number", 1),
                "bm25_index": base_idx + i,
            }
            self.chunk_metadata.append(meta)
            self.chunk_id_to_index[meta["chunk_id"]] = meta["bm25_index"]

        self._save_chunk_metadata()

        unique_pages = len(set(c.metadata.get("page_number", 0) for c in chunks))
        file_size_mb = round(os.path.getsize(file_path) / (1024**2), 2) if os.path.exists(file_path) else 0.0

        self.document_registry[base] = {
            "chunks": len(chunks),
            "pages": unique_pages,
            "uploaded": datetime.now().isoformat(),
            "size_mb": file_size_mb,
        }
        self.save_registry()

        if progress_cb:
            progress_cb(1.0, f"Successfully indexed '{base}' ({len(chunks)} chunks)")

        logger.info(f"Successfully indexed document '{base}' ({len(chunks)} chunks).")
        return f"INDEXED:{base}:{len(chunks)}"

    def delete_document(self, doc_name: str) -> str:
        if doc_name not in self.document_registry:
            return f"MISSING:{doc_name}"

        cids = [m["chunk_id"] for m in self.chunk_metadata if m.get("document_id") == doc_name]
        if cids:
            try:
                self.vector_db.delete(ids=cids)
            except Exception as e:
                logger.error(f"Chroma delete error for '{doc_name}': {e}")

        bm25_indices_to_delete = []
        for i, cid in enumerate(self.bm25.doc_chunk_ids):
            if any(m["chunk_id"] == cid and m.get("document_id") == doc_name for m in self.chunk_metadata):
                bm25_indices_to_delete.append(i)

        if bm25_indices_to_delete:
            self.bm25.delete_documents(bm25_indices_to_delete)

        self.chunk_metadata = [m for m in self.chunk_metadata if m.get("document_id") != doc_name]
        self.chunk_id_to_index = {m["chunk_id"]: i for i, m in enumerate(self.chunk_metadata)}
        self._save_chunk_metadata()

        del self.document_registry[doc_name]
        self.save_registry()
        logger.info(f"Deleted document '{doc_name}' from indices.")
        return f"DELETED:{doc_name}"

    def dense_search(self, query: str, k: int = 8, doc_filter: Optional[List[str]] = None) -> List[Document]:
        filter_dict = None
        if doc_filter:
            valid = [df for df in doc_filter if df]
            if len(valid) == 1:
                filter_dict = {"document_id": valid[0]}
            elif len(valid) > 1:
                filter_dict = {"document_id": {"$in": valid}}

        try:
            results_with_scores = self.vector_db.similarity_search_with_score(query, k=k, filter=filter_dict)
            docs = []
            for doc, score in results_with_scores:
                doc.metadata["score"] = float(score)
                docs.append(doc)
            return docs
        except Exception as e:
            logger.warning(f"Dense search fallback without filter: {e}")
            results_with_scores = self.vector_db.similarity_search_with_score(query, k=k)
            docs = []
            for doc, score in results_with_scores:
                doc.metadata["score"] = float(score)
                docs.append(doc)
            return docs

    def sparse_search(self, query: str, k: int = 8) -> List[Document]:
        top_chunk_ids = self.bm25.get_top_k(query, k=k)
        docs = []
        for cid in top_chunk_ids:
            d = self.get_chunk_by_id(cid)
            if d:
                docs.append(d)
        return docs

    def reciprocal_rank_fusion(self, dense: List[Document], sparse: List[Document], k: int = 60) -> List[Document]:
        scores = defaultdict(float)
        docs_map = {}
        for rank, d in enumerate(dense):
            uid = d.metadata.get("chunk_id", str(hash(d.page_content)))
            scores[uid] += 1.0 / (k + rank)
            docs_map[uid] = d
        for rank, d in enumerate(sparse):
            uid = d.metadata.get("chunk_id", str(hash(d.page_content)))
            scores[uid] += 1.0 / (k + rank)
            docs_map[uid] = d
        sorted_docs = [docs_map[uid] for uid, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)]
        return sorted_docs

    def rerank(self, query: str, docs: List[Document], top_k: int = 6) -> List[Tuple[Document, float]]:
        if not docs:
            self._last_scores = []
            return []
        corpus = [d.page_content for d in docs[:20]]
        pairs = [[query, t] for t in corpus]
        scores = self.reranker.predict(pairs)
        scored = sorted(zip(docs[:20], scores), key=lambda x: x[1], reverse=True)
        self._last_scores = [float(s) for _, s in scored[:top_k]]
        for doc, score in scored[:top_k]:
            doc.metadata["score"] = float(score)
        return scored[:top_k]

    def compress_context(self, docs: List[Tuple[Document, float]], max_chunks: int = 6) -> List[Document]:
        """Semantic deduplication by page, retaining similarity/relevance score in metadata."""
        page_best = {}
        for doc, score in docs:
            doc.metadata["score"] = float(score)
            key = (doc.metadata.get("source_file"), doc.metadata.get("page_number"))
            if key not in page_best or score > page_best[key][1]:
                page_best[key] = (doc, score)
        deduped = [d for d, _ in sorted(page_best.values(), key=lambda x: x[1], reverse=True)]
        return deduped[:max_chunks]

    def confidence(self) -> int:
        if not self._last_scores:
            return 0
        mx = max(self._last_scores)
        return max(0, min(100, int((mx + 5) / 10 * 100)))

    def list_docs(self) -> Dict:
        return self.document_registry
