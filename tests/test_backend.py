"""Comprehensive Backend Verification Suite for EKIP Platform using unittest."""

import os
import unittest
import tempfile
from pathlib import Path
from config.settings import Config
from core.logger import get_logger
from core.loader import DocumentLoader
from core.memory import ConversationMemory
from analytics.telemetry import TelemetryTracker
from api.endpoints import PlatformAPI


class TestEKIPBackend(unittest.TestCase):
    """EKIP Backend Unit and Integration Test Case."""

    def test_01_config_validation(self):
        """Verify configuration settings and defaults."""
        self.assertEqual(Config.APP_TITLE, "Educational Knowledge Intelligence Platform (EKIP)")
        self.assertIn("all-MiniLM-L6-v2", Config.EMBEDDING_MODEL)
        self.assertEqual(Config.RERANKER_MODEL, "cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.assertGreaterEqual(len(Config.LLM_FALLBACK_MODELS), 3)

    def test_02_loguru_logging(self):
        """Verify Loguru structured logger operates without throwing exceptions."""
        logger = get_logger("test.component")
        logger.info("Testing Loguru logger integration.")
        self.assertTrue(os.path.exists(Config.LOG_DIR))

    def test_03_document_loader(self):
        """Test multi-format document loading and chunk metadata tags."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            test_file = Path(tmp_dir) / "sample_doc.txt"
            test_file.write_text("Educational Knowledge Intelligence Platform enables RAG search at scale.\n" * 20, encoding="utf-8")

            loader = DocumentLoader(chunk_size=200, chunk_overlap=20)
            raw_docs = loader.load_file(str(test_file))
            self.assertGreater(len(raw_docs), 0)

            chunks = loader.chunk_documents(raw_docs, test_file.name)
            self.assertGreater(len(chunks), 0)
            first_chunk = chunks[0]
            self.assertIn("source_file", first_chunk.metadata)
            self.assertIn("document_id", first_chunk.metadata)
            self.assertIn("chunk_id", first_chunk.metadata)
            self.assertIn("page_number", first_chunk.metadata)

    def test_04_conversation_memory(self):
        """Test SQLite database initialization, WAL mode, message persistence, and feedback."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            db_file = Path(tmp_dir) / "test_memory.db"
            mem = ConversationMemory(str(db_file))

            cid = mem.create_conversation("Unit Test Conversation")
            self.assertEqual(len(cid), 8)

            mem.add_message(cid, "user", "What is EKIP?")
            mem.add_message(
                cid,
                "assistant",
                "EKIP is an AI-powered educational platform.",
                citations=[{"source_file": "doc1.pdf", "page": 1, "score": 0.95}],
                confidence=95,
                latency_ms=120,
            )

            msgs = mem.get_messages(cid)
            self.assertEqual(len(msgs), 2)
            self.assertEqual(msgs[0]["role"], "user")
            self.assertEqual(msgs[1]["role"], "assistant")
            self.assertEqual(msgs[1]["confidence"], 95)

            msg_id = msgs[1]["id"]
            mem.record_feedback(msg_id, "thumbs_up")
            updated_msgs = mem.get_messages(cid)
            self.assertEqual(updated_msgs[1]["feedback"], "thumbs_up")

    def test_05_telemetry_tracker(self):
        """Test telemetry metric calculations and database logging."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            db_file = Path(tmp_dir) / "test_telemetry.db"
            mem = ConversationMemory(str(db_file))

            tokens = TelemetryTracker.calculate_estimated_tokens("What is RAG architecture?")
            self.assertGreater(tokens, 0)

            metrics = TelemetryTracker.record_query_metrics(
                memory_instance=mem,
                query="Explain CRAG fallback mechanism",
                intent="QA",
                confidence=90,
                faithfulness=0.92,
                blocked=False,
                latency_ms=350,
                agent_trace=["RetrievalAgent", "CRAGAgent", "SynthesisAgent"],
                crag_used=True,
                web_results_count=2,
            )

            self.assertEqual(metrics["intent"], "QA")
            self.assertEqual(metrics["latency_ms"], 350)
            self.assertTrue(metrics["crag_used"])
            self.assertEqual(mem.get_total_queries(), 1)

    def test_06_platform_api(self):
        """Test health check and system API report."""
        health = PlatformAPI.get_health_status(None, Config)
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(health["app_title"], "Educational Knowledge Intelligence Platform (EKIP)")



if __name__ == "__main__":
    unittest.main()
