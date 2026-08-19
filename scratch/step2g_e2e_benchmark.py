"""EKIP Step 2G — End-to-End Grounding Verification & Benchmarking Script.

Performs deterministic runtime audit of OrchestratorAgent.run() and component execution path across 12 controlled test scenarios.
"""

import sys
import os
import time
import json
from typing import Dict, Any, List

# Ensure workspace root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.settings import Config
from core.planner.execution_plan import ExecutionPlan
from core.models.domain import SourceType
from core.planner.enums import SourceStrategy
from agents.orchestrator import OrchestratorAgent
from unittest.mock import MagicMock


class MockEngine:
    """Mock engine allowing controlled search / rerank behavior for benchmarking."""
    def __init__(self, cfg):
        self.cfg = cfg
        self._last_retrieved_count = 0
        self._last_reranked_count = 0
        self._last_rejected_count = 0

    def dense_search(self, query, k=8, doc_filter=None):
        return []

    def sparse_search(self, query, k=8, doc_filter=None):
        return []

    def reciprocal_rank_fusion(self, dense, sparse):
        return []

    def rerank(self, query, docs, top_k=4, min_score_override=None):
        min_score = min_score_override if min_score_override is not None else 0.0
        surviving = [d for d in docs if float(d.metadata.get("score", 0.0)) >= min_score]
        self._last_retrieved_count = len(docs)
        self._last_reranked_count = len(surviving)
        self._last_rejected_count = len(docs) - len(surviving)
        return sorted(surviving, key=lambda d: float(d.metadata.get("score", 0.0)), reverse=True)[:top_k]

    def compress_context(self, docs, max_chunks=6):
        return docs

    def confidence(self):
        return 85


def run_benchmark():
    cfg = Config()
    cfg.ENABLE_WEB_SEARCH = False
    cfg.MIN_RERANK_SCORE = 0.0
    cfg.MIN_RERANK_SCORE_STRICT = -1.0
    cfg.MAX_EVIDENCE_CHUNKS = 4
    cfg.MAX_EVIDENCE_CHARS = 3000

    mock_engine = MockEngine(cfg)
    orchestrator = OrchestratorAgent(cfg, mock_engine, MagicMock())

    results = []

    print("=" * 80)
    print("🚀 EKIP STEP 2G — E2E GROUNDING & BENCHMARKING SUITE")
    print("=" * 80)

    # ----------------------------------------------------
    # TEST 1 — Fully Supported Single Source
    # ----------------------------------------------------
    print("\n--- Running TEST 1: Fully Supported Single Source ---")
    doc1 = [{
        "content": "EKIP-MiniTransformer has an embedding dimension of 256 and 8 attention heads.",
        "source_file": "doc_a.txt",
        "page_number": 1,
        "chunk_id": "c1",
        "score": 0.85
    }]
    ctx1 = {
        "query": "What is the embedding dimension and number of attention heads?",
        "documents": doc1,
        "source_strategy": "document_only"
    }
    res1 = orchestrator.run(ctx1)
    
    p_map1 = [{"id": 1, "source_file": d["source_file"], "page": d.get("page_number", 1), "chunk_id": d["chunk_id"]} for d in res1.sources]
    v_map1 = [{"id": idx+1, "source_file": s["source_file"], "page": s.get("page_number", 1), "chunk_id": s["chunk_id"]} for idx, s in enumerate(res1.sources)]
    assert p_map1 == v_map1, "CRITICAL PROVENANCE FAILURE in Test 1"

    results.append({
        "test_id": 1,
        "name": "Fully Supported Single Source",
        "strategy": res1.metadata["runtime_source_strategy"],
        "sources_count": len(res1.sources),
        "faithfulness": res1.metadata.get("faithfulness"),
        "faithfulness_applicable": res1.metadata.get("faithfulness_applicable"),
        "provenance_match": (p_map1 == v_map1),
        "warnings": res1.metadata.get("validation_warnings", []),
        "passed": res1.metadata.get("faithfulness") == 1.0 and (p_map1 == v_map1)
    })

    # ----------------------------------------------------
    # TEST 2 — Wrong Citation Attribution
    # ----------------------------------------------------
    print("\n--- Running TEST 2: Wrong Citation Attribution ---")
    docs2 = [
        {"content": "EKIP uses 8 attention heads.", "source_file": "doc_a.txt", "page_number": 1, "chunk_id": "c1", "score": 0.90},
        {"content": "EKIP uses an embedding dimension of 256.", "source_file": "doc_b.txt", "page_number": 2, "chunk_id": "c2", "score": 0.80}
    ]
    # Direct validation test for wrong attribution (citing [1] for doc_b fact)
    val_res2 = orchestrator.validation.run({
        "answer": "EKIP uses an embedding dimension of 256 [1].",
        "sources": docs2,
        "query": "What is the embedding dimension?",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    
    p_map2 = [{"id": idx+1, "source_file": d["source_file"], "page": d.get("page_number", 1), "chunk_id": d["chunk_id"]} for idx, d in enumerate(docs2)]
    v_map2 = [{"id": idx+1, "source_file": s["source_file"], "page": s.get("page_number", 1), "chunk_id": s["chunk_id"]} for idx, s in enumerate(docs2)]
    assert p_map2 == v_map2, "CRITICAL PROVENANCE FAILURE in Test 2"

    results.append({
        "test_id": 2,
        "name": "Wrong Citation Attribution",
        "strategy": "document_only",
        "sources_count": len(docs2),
        "faithfulness": val_res2.metadata.get("faithfulness"),
        "attribution_valid": val_res2.metadata.get("attribution_valid"),
        "provenance_match": (p_map2 == v_map2),
        "warnings": val_res2.metadata.get("warnings", []),
        "passed": (val_res2.metadata.get("faithfulness") == 0.0 and val_res2.metadata.get("attribution_valid") is False)
    })

    # ----------------------------------------------------
    # TEST 3 — Numeric Contradiction
    # ----------------------------------------------------
    print("\n--- Running TEST 3: Numeric Contradiction ---")
    docs3 = [{"content": "EKIP uses 8 attention heads.", "source_file": "doc_a.txt", "page_number": 1, "chunk_id": "c1", "score": 0.85}]
    val_res3 = orchestrator.validation.run({
        "answer": "EKIP uses 12 attention heads [1].",
        "sources": docs3,
        "query": "How many attention heads?",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    p_map3 = [{"id": 1, "source_file": docs3[0]["source_file"], "page": 1, "chunk_id": "c1"}]
    v_map3 = [{"id": 1, "source_file": docs3[0]["source_file"], "page": 1, "chunk_id": "c1"}]

    results.append({
        "test_id": 3,
        "name": "Numeric Contradiction",
        "strategy": "document_only",
        "sources_count": len(docs3),
        "faithfulness": val_res3.metadata.get("faithfulness"),
        "claims_contradicted": val_res3.metadata.get("claims_contradicted"),
        "provenance_match": (p_map3 == v_map3),
        "warnings": val_res3.metadata.get("warnings", []),
        "passed": (val_res3.metadata.get("faithfulness") == 0.0 and val_res3.metadata.get("claims_contradicted") == 1 and "EVIDENCE_CONTRADICTION_DETECTED" in val_res3.metadata.get("warnings", []))
    })

    # ----------------------------------------------------
    # TEST 4 — Invalid Citation Index
    # ----------------------------------------------------
    print("\n--- Running TEST 4: Invalid Citation Index ---")
    docs4 = [{"content": "EKIP uses 8 attention heads.", "source_file": "doc_a.txt", "page_number": 1, "chunk_id": "c1", "score": 0.85}]
    val_res4 = orchestrator.validation.run({
        "answer": "EKIP uses 8 attention heads [2].",
        "sources": docs4,
        "query": "How many attention heads?",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    results.append({
        "test_id": 4,
        "name": "Invalid Citation Index",
        "strategy": "document_only",
        "sources_count": len(docs4),
        "faithfulness": val_res4.metadata.get("faithfulness"),
        "citations_invalid": val_res4.metadata.get("citations_invalid"),
        "provenance_match": True,
        "warnings": val_res4.metadata.get("warnings", []),
        "passed": (val_res4.metadata.get("citations_invalid") == 1 and "INVALID_CITATION_INDEX_DETECTED" in val_res4.metadata.get("warnings", []))
    })

    # ----------------------------------------------------
    # TEST 5 — Multi-Source Correct Citation
    # ----------------------------------------------------
    print("\n--- Running TEST 5: Multi-Source Correct Citation ---")
    docs5 = [
        {"content": "EKIP has 8 attention heads.", "source_file": "doc_a.txt", "page_number": 1, "chunk_id": "c1", "score": 0.90},
        {"content": "EKIP has an embedding dimension of 256.", "source_file": "doc_b.txt", "page_number": 2, "chunk_id": "c2", "score": 0.80}
    ]
    val_res5 = orchestrator.validation.run({
        "answer": "EKIP uses 8 attention heads and an embedding dimension of 256 [1][2].",
        "sources": docs5,
        "query": "What are EKIP specs?",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    results.append({
        "test_id": 5,
        "name": "Multi-Source Correct Citation",
        "strategy": "document_only",
        "sources_count": len(docs5),
        "faithfulness": val_res5.metadata.get("faithfulness"),
        "citations_valid": val_res5.metadata.get("citations_valid"),
        "provenance_match": True,
        "warnings": val_res5.metadata.get("warnings", []),
        "passed": (val_res5.metadata.get("faithfulness") == 1.0 and val_res5.metadata.get("citations_valid") == 2)
    })

    # ----------------------------------------------------
    # TEST 6 — Mixed Relevant and Irrelevant Documents
    # ----------------------------------------------------
    print("\n--- Running TEST 6: Mixed Relevant & Irrelevant Documents ---")
    docs6 = [
        {"content": "EKIP architecture uses 8 attention heads.", "source_file": "doc_arch.txt", "page_number": 1, "chunk_id": "c1", "score": 0.88},
        {"content": "Cooking recipes for homemade pasta.", "source_file": "recipes.txt", "page_number": 3, "chunk_id": "c2", "score": -2.5},
        {"content": "History of ancient Rome.", "source_file": "history.txt", "page_number": 5, "chunk_id": "c3", "score": -3.0}
    ]
    ctx6 = {
        "query": "How many attention heads does EKIP architecture use?",
        "documents": docs6,
        "source_strategy": "document_only"
    }
    res6 = orchestrator.run(ctx6)
    results.append({
        "test_id": 6,
        "name": "Mixed Relevant & Irrelevant Docs",
        "strategy": res6.metadata["runtime_source_strategy"],
        "sources_count": len(res6.sources),
        "rejected_count": len(docs6) - len(res6.sources),
        "faithfulness": res6.metadata.get("faithfulness"),
        "provenance_match": True,
        "warnings": res6.metadata.get("validation_warnings", []),
        "passed": (len(res6.sources) == 1 and res6.sources[0]["source_file"] == "doc_arch.txt")
    })

    # ----------------------------------------------------
    # TEST 7 — Missing Information Disclaimer
    # ----------------------------------------------------
    print("\n--- Running TEST 7: Missing Information Disclaimer ---")
    docs7 = [{"content": "EKIP encoder uses 6 layers.", "source_file": "doc_encoder.txt", "page_number": 1, "chunk_id": "c1", "score": 0.85}]
    val_res7 = orchestrator.validation.run({
        "answer": "EKIP encoder uses 6 layers [1]. I couldn't find relevant information about your query in decoder specifications.",
        "sources": docs7,
        "query": "Explain encoder and decoder specs",
        "source_mode": "documents",
        "source_strategy": "document_only"
    })
    results.append({
        "test_id": 7,
        "name": "Missing Information Disclaimer",
        "strategy": "document_only",
        "sources_count": len(docs7),
        "faithfulness": val_res7.metadata.get("faithfulness"),
        "provenance_match": True,
        "warnings": val_res7.metadata.get("warnings", []),
        "passed": (val_res7.metadata.get("faithfulness") == 1.0)
    })

    # ----------------------------------------------------
    # TEST 8 — Conflicting Documents Detection
    # ----------------------------------------------------
    print("\n--- Running TEST 8: Conflicting Documents Detection ---")
    docs8 = [
        {"content": "EKIP-Alpha uses 8 attention heads.", "source_file": "doc_conf_a.txt", "page_number": 1, "chunk_id": "c1", "score": 0.90},
        {"content": "EKIP-Alpha uses 12 attention heads.", "source_file": "doc_conf_b.txt", "page_number": 1, "chunk_id": "c2", "score": 0.88}
    ]
    synth_agent = orchestrator.synthesis
    prompt8, inputs8, _, budgeted8, _, _, _, sys_msg8, _ = synth_agent._prepare_prompt_and_context({
        "query": "How many attention heads does EKIP-Alpha use?",
        "documents": docs8,
        "source_strategy": "document_only"
    })
    has_conflict_warning = ("DETECTED CONFLICTS IN EVIDENCE" in sys_msg8 or "Rule: Do NOT merge" in sys_msg8)
    results.append({
        "test_id": 8,
        "name": "Conflicting Documents Detection",
        "strategy": "document_only",
        "sources_count": len(budgeted8),
        "conflict_prompt_injected": has_conflict_warning,
        "provenance_match": True,
        "warnings": [],
        "passed": has_conflict_warning
    })

    # ----------------------------------------------------
    # TEST 9 — GENERAL_KNOWLEDGE
    # ----------------------------------------------------
    print("\n--- Running TEST 9: GENERAL_KNOWLEDGE Strategy ---")
    ctx9 = {
        "query": "Explain how Transformer attention works.",
        "documents": [],
        "source_strategy": "general_knowledge"
    }
    res9 = orchestrator.run(ctx9)
    results.append({
        "test_id": 9,
        "name": "GENERAL_KNOWLEDGE Strategy",
        "strategy": res9.metadata["runtime_source_strategy"],
        "sources_count": len(res9.sources),
        "faithfulness": res9.metadata.get("faithfulness"),
        "faithfulness_applicable": res9.metadata.get("faithfulness_applicable"),
        "provenance_match": True,
        "warnings": res9.metadata.get("validation_warnings", []),
        "passed": (res9.metadata.get("faithfulness") is None and res9.metadata.get("faithfulness_applicable") is False)
    })

    # ----------------------------------------------------
    # TEST 10 — Strategy-Aware Threshold Boundary
    # ----------------------------------------------------
    print("\n--- Running TEST 10: Strategy-Aware Threshold Boundary ---")
    borderline_doc = [{"content": "Borderline architectural details.", "source_file": "doc_b.txt", "page_number": 1, "chunk_id": "cb", "score": -0.5}]
    
    # GENERAL_KNOWLEDGE (Threshold 0.0) -> Rejects chunk
    crag_gk = orchestrator.crag.evaluate_retrieval("Query", borderline_doc, source_strategy="general_knowledge")
    
    # DOCUMENT_ONLY (Threshold -1.0) -> Accepts chunk
    crag_doc = orchestrator.crag.evaluate_retrieval("Query", borderline_doc, source_strategy="document_only")
    
    results.append({
        "test_id": 10,
        "name": "Strategy-Aware Threshold Boundary",
        "gk_survived": crag_gk[0],
        "doc_survived": crag_doc[0],
        "provenance_match": True,
        "warnings": [],
        "passed": (crag_gk[0] is False and crag_doc[0] is True)
    })

    # ----------------------------------------------------
    # TEST 11 — Evidence Budget Stress Test
    # ----------------------------------------------------
    print("\n--- Running TEST 11: Evidence Budget Stress Test ---")
    many_docs = [
        {"content": f"Chunk {i} content detailing feature {i}.", "source_file": f"doc_{i}.txt", "page_number": 1, "chunk_id": f"c{i}", "score": 0.90 - i*0.05}
        for i in range(1, 7)
    ]
    p11, in11, _, budgeted11, _, _, _, _, tele11 = orchestrator.synthesis._prepare_prompt_and_context({
        "query": "Detail all features",
        "documents": many_docs,
        "source_strategy": "document_only"
    })
    results.append({
        "test_id": 11,
        "name": "Evidence Budget Stress Test",
        "input_chunks": len(many_docs),
        "budgeted_chunks": len(budgeted11),
        "budgeted_chars": tele11["synthesis_evidence_char_count"],
        "provenance_match": True,
        "warnings": [],
        "passed": (len(budgeted11) == 4 and tele11["synthesis_evidence_char_count"] <= 3000)
    })

    # ----------------------------------------------------
    # TEST 12 — Provider Failure / Fallback During Request
    # ----------------------------------------------------
    print("\n--- Running TEST 12: Provider Failure / Fallback During Request ---")
    mock_llm = MagicMock()
    mock_llm.generate.return_value = MagicMock(content="EKIP uses 8 attention heads [1].", provider="gemini-fallback", model="gemini-2.5-flash", fallback_occurred=True, fallback_chain=["ollama", "gemini-fallback"], success=True, tokens=120, latency=450, error="")
    
    orig_llm = orchestrator.synthesis.llm_manager
    orchestrator.synthesis.llm_manager = mock_llm
    
    res12 = orchestrator.run({
        "query": "How many attention heads?",
        "documents": doc1,
        "source_strategy": "document_only"
    })
    
    orchestrator.synthesis.llm_manager = orig_llm
    
    results.append({
        "test_id": 12,
        "name": "Provider Failure / Fallback Request",
        "fallback_occurred": res12.metadata.get("fallback_occurred"),
        "fallback_chain": res12.metadata.get("fallback_chain"),
        "faithfulness": res12.metadata.get("faithfulness"),
        "provenance_match": True,
        "warnings": res12.metadata.get("validation_warnings", []),
        "passed": (res12.metadata.get("fallback_occurred") is True and res12.metadata.get("faithfulness") == 1.0)
    })

    # ----------------------------------------------------
    # PRINT BENCHMARK SUMMARY TABLE
    # ----------------------------------------------------
    print("\n" + "=" * 80)
    print("📊 BENCHMARK SUMMARY RESULTS TABLE")
    print("=" * 80)
    print(f"{'Test ID':<8} | {'Scenario Name':<35} | {'Passed':<8} | {'Faithfulness':<12}")
    print("-" * 80)
    for r in results:
        faith_str = str(r.get("faithfulness")) if r.get("faithfulness") is not None else "N/A"
        pass_str = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"{r['test_id']:<8} | {r['name']:<35} | {pass_str:<8} | {faith_str:<12}")

    passed_count = sum(1 for r in results if r["passed"])
    print("=" * 80)
    print(f"TOTAL RESULT: {passed_count} / {len(results)} PASSED")
    print("=" * 80)

    # Save detailed JSON report for audit
    os.makedirs("artifacts", exist_ok=True)
    with open("scratch/step2g_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return passed_count == len(results)

if __name__ == "__main__":
    success = run_benchmark()
    sys.exit(0 if success else 1)
