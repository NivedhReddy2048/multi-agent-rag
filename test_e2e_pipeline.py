"""End-to-end integration and architectural unit test suite for MultiAgentRAG system."""

import os
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from config import Config
from core.engine import BaseRAGEngine, IncrementalBM25
from core.memory import ConversationMemory
from core.loader import DocumentLoader
from langchain_core.documents import Document


class TestMultiAgentRAG(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Config.validate()
        cls.engine = BaseRAGEngine(Config)
        cls.memory = ConversationMemory(Config.OBSERVABILITY_DB)

    def test_01_bm25_chunk_id_alignment(self):
        bm25 = IncrementalBM25(str(Config.DATA_DIR / "test_bm25.pkl"))
        texts = ["Revenue grew 25% in Q3 due to cloud computing adoption.", "Cybersecurity incidents decreased by 14%."]
        cids = ["chunk_rev_1", "chunk_sec_1"]
        bm25.add_documents(texts, chunk_ids=cids)

        hits = bm25.get_top_k("cloud computing revenue", k=2)
        self.assertIn("chunk_rev_1", hits)

        bm25.delete_documents([0])
        hits_after_delete = bm25.get_top_k("cybersecurity", k=1)
        self.assertIn("chunk_sec_1", hits_after_delete)

    def test_02_ingest_and_retrieval(self):
        doc1 = Document(page_content="Enterprise AI Architecture utilizes microservices and vector stores.", metadata={"chunk_id": "test_ai_1", "source_file": "ai_arch.txt", "document_id": "ai_arch.txt", "page_number": 1})
        res = self.engine.ingest("ai_arch.txt", [doc1])
        self.assertTrue(res.startswith("INDEXED") or res.startswith("EXISTS"))

        dense_hits = self.engine.dense_search("microservices architecture", k=2)
        self.assertTrue(len(dense_hits) > 0)

        sparse_hits = self.engine.sparse_search("vector stores", k=2)
        self.assertTrue(len(sparse_hits) > 0)

    def test_03_sqlite_memory_telemetry(self):
        cid = self.memory.create_conversation("Integration Test Chat")
        self.memory.add_message(cid, "user", "What is enterprise architecture?")
        self.memory.add_message(cid, "assistant", "Enterprise architecture is...", confidence=95, latency_ms=120)

        messages = self.memory.get_messages(cid)
        self.assertEqual(len(messages), 2)

        self.memory.log_query_analytics(
            query="test architecture query",
            intent="QA",
            confidence=90,
            faithfulness=0.95,
            blocked=False,
            latency_ms=250,
            agent_trace=["Intent: QA", "RetrievalAgent"],
            crag_used=False
        )

        total_q = self.memory.get_total_queries()
        self.assertGreater(total_q, 0)


if __name__ == "__main__":
    unittest.main()
