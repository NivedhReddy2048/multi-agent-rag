"""EKIP Phase 6C — Real User Journey & Query Quality Audit Suite

Executes real runtime queries for categories C1 through C12 against the full EKIP pipeline:
Streamlit UI equivalent -> Planning Graph (chat_planning mode) -> OrchestratorAgent -> RetrievalAgent -> CRAGAgent -> SynthesisAgent -> ValidationAgent -> AgentResult -> AgentResponseAdapter.
"""

import os
import sys
import time
import json
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from config import Config
from core.engine import BaseRAGEngine
from core.memory import ConversationMemory
from core.logger import get_logger
from core.documents import save_user_document
from graph.builder import create_ekip_planning_graph
from agents.orchestrator import OrchestratorAgent
from core.synthesis.agent_response_adapter import agent_response_adapter

logger = get_logger("phase6c_audit")


from langchain_core.documents import Document


def setup_acceptance_documents():
    """Ingest controlled test documents into local ChromaDB for testing."""
    cfg = Config()
    engine = BaseRAGEngine._instance or BaseRAGEngine(cfg)

    doc1_filename = "doc_a_architecture_overview.txt"
    doc1_content = (
        "EKIP Neural System Overview:\n"
        "The model architecture uses a transformer backbone with 16 attention heads and 24 hidden layers. "
        "The embedding dimension is configured to 1024, and the dropout rate is strictly 0.15. "
        "All parameters are optimized using AdamW with cosine learning rate schedule."
    )
    doc1_chunk = Document(
        page_content=doc1_content,
        metadata={
            "chunk_id": f"{doc1_filename}_0",
            "source_file": doc1_filename,
            "document_id": doc1_filename,
            "filename": doc1_filename,
            "page_number": 1,
        }
    )
    engine.ingest(doc1_filename, [doc1_chunk])
    save_user_document(
        user_id="audit_user",
        filename=doc1_filename,
        title="EKIP Neural System Overview",
        doc_type="txt",
        size_bytes=len(doc1_content.encode("utf-8")),
        chunks=[doc1_chunk]
    )

    doc2_filename = "doc_b_hardware_cluster.txt"
    doc2_content = (
        "Server Hardware Infrastructure:\n"
        "The cluster consists of 32 nodes, each equipped with 8 NVIDIA H100 GPUs (80GB VRAM each). "
        "System memory is 1.5 TB DDR5 ECC RAM per node. Network interconnect is 400 Gbps InfiniBand. "
        "Power supply units are rated at 3000W redundant 80-Plus Titanium."
    )
    doc2_chunk = Document(
        page_content=doc2_content,
        metadata={
            "chunk_id": f"{doc2_filename}_0",
            "source_file": doc2_filename,
            "document_id": doc2_filename,
            "filename": doc2_filename,
            "page_number": 1,
        }
    )
    engine.ingest(doc2_filename, [doc2_chunk])
    save_user_document(
        user_id="audit_user",
        filename=doc2_filename,
        title="Server Hardware Infrastructure",
        doc_type="txt",
        size_bytes=len(doc2_content.encode("utf-8")),
        chunks=[doc2_chunk]
    )

    doc3_filename = "doc_c_conflicting_spec.txt"
    doc3_content = (
        "Legacy Model Specification:\n"
        "In contrast to newer builds, the legacy build uses 8 attention heads, 12 hidden layers, "
        "and an embedding dimension of 512 with a dropout rate of 0.05."
    )
    doc3_chunk = Document(
        page_content=doc3_content,
        metadata={
            "chunk_id": f"{doc3_filename}_0",
            "source_file": doc3_filename,
            "document_id": doc3_filename,
            "filename": doc3_filename,
            "page_number": 1,
        }
    )
    engine.ingest(doc3_filename, [doc3_chunk])
    save_user_document(
        user_id="audit_user",
        filename=doc3_filename,
        title="Legacy Model Specification",
        doc_type="txt",
        size_bytes=len(doc3_content.encode("utf-8")),
        chunks=[doc3_chunk]
    )

    logger.info("Successfully ingested Phase 6C test documents.")
    return doc1_filename, doc2_filename, doc3_filename


def run_single_user_journey_turn(
    query: str,
    doc_filter: Optional[List[str]] = None,
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Simulates a complete real user journey turn through Streamlit logic."""
    if history is None:
        history = []

    planning_graph = create_ekip_planning_graph()
    
    # 1. Invoke planning graph in chat_planning mode (skip standalone graph synthesis)
    plan_state = planning_graph.invoke({
        "question": query,
        "conversation_history": history,
        "execution_mode": "chat_planning",
        "skip_synthesis": True,
        "selected_docs": doc_filter or [],
    })
    
    exec_plan = plan_state.execution_plan
    edu_meta = plan_state.provider_metadata.get("educational_response") or plan_state.educational_response
    if hasattr(edu_meta, "dict"):
        edu_meta = edu_meta.dict()

    ctx = {
        "query": query,
        "history": history,
        "filters": {"doc_filter": doc_filter} if doc_filter else {},
        "doc_filter": doc_filter,
        "execution_plan": exec_plan,
        "educational_response": edu_meta,
        "plan_state": plan_state,
    }

    cfg = Config()
    engine = BaseRAGEngine._instance or BaseRAGEngine(cfg)
    memory = ConversationMemory(cfg.OBSERVABILITY_DB)
    orch = OrchestratorAgent(cfg, engine, memory)
    t0 = time.time()
    result = orch.run(ctx)
    latency = round((time.time() - t0) * 1000, 2)

    # Educational response adapter transformation
    edu_response = agent_response_adapter.compose_from_agent_result(result)
    result.metadata["educational_response"] = edu_response

    return {
        "query": query,
        "doc_filter": doc_filter,
        "exec_plan": exec_plan.dict() if exec_plan and hasattr(exec_plan, "dict") else {},
        "result_content": result.content,
        "confidence": result.confidence,
        "response_status": result.metadata.get("response_status", "UNKNOWN"),
        "source_mode": result.metadata.get("source_mode", "none"),
        "provider": result.metadata.get("provider", "none"),
        "model": result.metadata.get("model", "none"),
        "retrieved_chunks_count": result.metadata.get("retrieved_chunks_count", 0),
        "citations_count": len(result.sources or []),
        "educational_response": edu_response,
        "latency_ms": latency,
        "agent_trace": result.agent_trace,
    }


def execute_phase_6c_audit():
    print("=" * 70)
    print("EKIP Phase 6C -- Real End-to-End User Journey & Query Quality Audit")
    print("=" * 70)

    doc1, doc2, doc3 = setup_acceptance_documents()
    results = {}

    # Category C1: Simple Document Explanation
    print("\n--- [C1] SIMPLE DOCUMENT EXPLANATION ---")
    c1_res = run_single_user_journey_turn(
        query="Explain the main concepts in this document.",
        doc_filter=[doc1]
    )
    print(f"Status: {c1_res['response_status']} | Provider: {c1_res['provider']} / {c1_res['model']}")
    print(f"Chunks: {c1_res['retrieved_chunks_count']} | Citations: {c1_res['citations_count']}")
    print(f"Explanation snippet: {c1_res['result_content'][:180]}...")
    results["C1"] = c1_res

    # Category C2: Exact Fact Retrieval
    print("\n--- [C2] EXACT FACT RETRIEVAL ---")
    c2_res = run_single_user_journey_turn(
        query="What is the embedding dimension in the document?",
        doc_filter=[doc1]
    )
    print(f"Status: {c2_res['response_status']} | Provider: {c2_res['provider']}")
    print(f"Chunks: {c2_res['retrieved_chunks_count']} | Citations: {c2_res['citations_count']}")
    print(f"Answer: {c2_res['result_content'][:180]}...")
    results["C2"] = c2_res

    # Category C3: Multi-Fact Query
    print("\n--- [C3] MULTI-FACT QUERY ---")
    c3_res = run_single_user_journey_turn(
        query="What are the hidden dimension, number of layers, and dropout value in doc_a_architecture_overview.txt?",
        doc_filter=[doc1]
    )
    print(f"Status: {c3_res['response_status']} | Provider: {c3_res['provider']}")
    print(f"Chunks: {c3_res['retrieved_chunks_count']} | Citations: {c3_res['citations_count']}")
    print(f"Answer: {c3_res['result_content'][:180]}...")
    results["C3"] = c3_res

    # Category C4: Multi-Document Comparison
    print("\n--- [C4] MULTI-DOCUMENT COMPARISON ---")
    c4_res = run_single_user_journey_turn(
        query="Compare the architecture described in doc_a_architecture_overview.txt with the server hardware in doc_b_hardware_cluster.txt.",
        doc_filter=[doc1, doc2]
    )
    print(f"Status: {c4_res['response_status']} | Provider: {c4_res['provider']}")
    print(f"Chunks: {c4_res['retrieved_chunks_count']} | Citations: {c4_res['citations_count']}")
    print(f"Answer: {c4_res['result_content'][:180]}...")
    results["C4"] = c4_res

    # Category C5: Conflicting Evidence
    print("\n--- [C5] CONFLICTING EVIDENCE ---")
    c5_res = run_single_user_journey_turn(
        query="How many attention heads does the model have across doc_a_architecture_overview.txt and doc_c_conflicting_spec.txt?",
        doc_filter=[doc1, doc3]
    )
    print(f"Status: {c5_res['response_status']} | Provider: {c5_res['provider']}")
    print(f"Chunks: {c5_res['retrieved_chunks_count']} | Citations: {c5_res['citations_count']}")
    print(f"Answer: {c5_res['result_content'][:180]}...")
    results["C5"] = c5_res

    # Category C6: Missing Document Information
    print("\n--- [C6] MISSING DOCUMENT INFORMATION ---")
    c6_res = run_single_user_journey_turn(
        query="What is the battery capacity of the server in doc_a_architecture_overview.txt?",
        doc_filter=[doc1]
    )
    print(f"Status: {c6_res['response_status']} | Provider: {c6_res['provider']}")
    print(f"Chunks: {c6_res['retrieved_chunks_count']} | Citations: {c6_res['citations_count']}")
    print(f"Answer: {c6_res['result_content'][:180]}...")
    results["C6"] = c6_res

    # Category C7: Irrelevant Selected Document
    print("\n--- [C7] IRRELEVANT SELECTED DOCUMENT ---")
    c7_res = run_single_user_journey_turn(
        query="Explain the attention mechanism used by the transformer from doc_b_hardware_cluster.txt.",
        doc_filter=[doc2]
    )
    print(f"Status: {c7_res['response_status']} | Provider: {c7_res['provider']}")
    print(f"Chunks: {c7_res['retrieved_chunks_count']} | Citations: {c7_res['citations_count']}")
    print(f"Answer: {c7_res['result_content'][:180]}...")
    results["C7"] = c7_res

    # Category C8: General Knowledge Query
    print("\n--- [C8] GENERAL KNOWLEDGE QUERY ---")
    c8_res = run_single_user_journey_turn(
        query="Explain entropy in information theory with a simple example.",
        doc_filter=[]
    )
    print(f"Status: {c8_res['response_status']} | Provider: {c8_res['provider']}")
    print(f"Mode: {c8_res['source_mode']} | Citations: {c8_res['citations_count']}")
    print(f"Answer: {c8_res['result_content'][:180]}...")
    results["C8"] = c8_res

    # Category C9: Follow-Up Conversation
    print("\n--- [C9] FOLLOW-UP CONVERSATION ---")
    t1_hist = [
        {"role": "user", "content": "What is attention in transformers?"},
        {"role": "assistant", "content": "Attention allows transformer models to dynamically weight input tokens."}
    ]
    c9_res = run_single_user_journey_turn(
        query="Give me a simple example of that.",
        doc_filter=[],
        history=t1_hist
    )
    print(f"Status: {c9_res['response_status']} | Provider: {c9_res['provider']}")
    print(f"Answer: {c9_res['result_content'][:180]}...")
    results["C9"] = c9_res

    # Category C10: Context Switching / Stale State
    print("\n--- [C10] CONTEXT SWITCHING / STALE STATE ---")
    t2_hist = [
        {"role": "user", "content": "What is in doc_a_architecture_overview.txt?"},
        {"role": "assistant", "content": "It describes 16 attention heads and 24 hidden layers."},
        {"role": "user", "content": "Explain entropy in information theory."},
        {"role": "assistant", "content": "Entropy measures uncertainty in a probability distribution."}
    ]
    c10_res = run_single_user_journey_turn(
        query="What server hardware is described in doc_b_hardware_cluster.txt?",
        doc_filter=[doc2],
        history=t2_hist
    )
    print(f"Status: {c10_res['response_status']} | Provider: {c10_res['provider']}")
    print(f"Chunks: {c10_res['retrieved_chunks_count']} | Citations: {c10_res['citations_count']}")
    print(f"Answer: {c10_res['result_content'][:180]}...")
    results["C10"] = c10_res

    # Category C11: Provider Failover / Router Verification
    print("\n--- [C11] PROVIDER FAILOVER ---")
    c11_res = run_single_user_journey_turn(
        query="Explain backpropagation in neural networks.",
        doc_filter=[]
    )
    print(f"Status: {c11_res['response_status']} | Provider: {c11_res['provider']} / {c11_res['model']}")
    print(f"Answer: {c11_res['result_content'][:180]}...")
    results["C11"] = c11_res

    # Category C12: Empty / Ambiguous Query
    print("\n--- [C12] EMPTY / AMBIGUOUS QUERY ---")
    c12_res = run_single_user_journey_turn(
        query="Explain this.",
        doc_filter=[]
    )
    print(f"Status: {c12_res['response_status']} | Provider: {c12_res['provider']}")
    print(f"Answer: {c12_res['result_content'][:180]}...")
    results["C12"] = c12_res

    # Save detailed JSON summary
    out_path = "scratch/phase6c_user_journey_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        # Convert non-serializable fields if any
        json.dump(results, f, indent=2, default=str)

    print("\n" + "=" * 70)
    print("PHASE 6C COMPLETED -- ALL 12 REAL USER JOURNEY TESTS EXECUTED")
    print(f"Saved results log to: {out_path}")
    print("=" * 70)


def test_phase6c_user_journey_audit():
    """Pytest wrapper to execute the Phase 6C user journey audit suite."""
    execute_phase_6c_audit()


if __name__ == "__main__":
    import traceback
    try:
        execute_phase_6c_audit()
    except BaseException as e:
        sys.stderr.write(f"EXCEPTIONAL ERROR IN PHASE 6C AUDIT: {e}\n")
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)
