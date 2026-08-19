import os
import sys
import json
import time
import re
from pathlib import Path
import pytest

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.settings import Config
from core.engine import BaseRAGEngine
from agents.orchestrator import OrchestratorAgent
from core.planner.enums import SourceStrategy
from langchain_core.documents import Document

def build_benchmark_engine():
    import tempfile
    
    cfg = Config()
    test_dir = tempfile.mkdtemp(prefix="ekip_bench_chroma_")
    cfg.CHROMA_PATH = os.path.join(test_dir, "chroma")
    
    engine = BaseRAGEngine(cfg)

    base_dir = Path(__file__).parent.parent / "scratch"
    doc_a_file = str(base_dir / "doc_a_transformer_spec.txt")
    doc_b_file = str(base_dir / "doc_b_encoder_spec.txt")
    doc_c_file = str(base_dir / "doc_c_database_indexing.txt")
    doc_conf_a_file = str(base_dir / "doc_conf_a.txt")
    doc_conf_b_file = str(base_dir / "doc_conf_b.txt")

    (base_dir / "doc_conf_a.txt").write_text("DocConfA: The EKIP-Alpha architecture uses 8 attention heads in total.", encoding="utf-8")
    (base_dir / "doc_conf_b.txt").write_text("DocConfB: The EKIP-Alpha architecture uses 12 attention heads in total.", encoding="utf-8")

    doc_a_text = Path(doc_a_file).read_text(encoding="utf-8")
    doc_b_text = Path(doc_b_file).read_text(encoding="utf-8")
    doc_c_text = Path(doc_c_file).read_text(encoding="utf-8")
    doc_conf_a_text = Path(doc_conf_a_file).read_text(encoding="utf-8")
    doc_conf_b_text = Path(doc_conf_b_file).read_text(encoding="utf-8")

    chunk_a = Document(page_content=doc_a_text, metadata={"source_file": "doc_a_transformer_spec.txt", "document_id": "doc_a_transformer_spec.txt", "page_number": 1, "chunk_id": "chunk_a_1"})
    chunk_b = Document(page_content=doc_b_text, metadata={"source_file": "doc_b_encoder_spec.txt", "document_id": "doc_b_encoder_spec.txt", "page_number": 1, "chunk_id": "chunk_b_1"})
    chunk_c = Document(page_content=doc_c_text, metadata={"source_file": "doc_c_database_indexing.txt", "document_id": "doc_c_database_indexing.txt", "page_number": 1, "chunk_id": "chunk_c_1"})
    chunk_conf_a = Document(page_content=doc_conf_a_text, metadata={"source_file": "doc_conf_a.txt", "document_id": "doc_conf_a.txt", "page_number": 1, "chunk_id": "chunk_conf_a_1"})
    chunk_conf_b = Document(page_content=doc_conf_b_text, metadata={"source_file": "doc_conf_b.txt", "document_id": "doc_conf_b.txt", "page_number": 1, "chunk_id": "chunk_conf_b_1"})

    engine.ingest(doc_a_file, [chunk_a])
    engine.ingest(doc_b_file, [chunk_b])
    engine.ingest(doc_c_file, [chunk_c])
    engine.ingest(doc_conf_a_file, [chunk_conf_a])
    engine.ingest(doc_conf_b_file, [chunk_conf_b])

    return engine, cfg

def evaluate_claims(answer, evidence_texts, is_doc_only):
    sentences = [s.strip() for s in re.split(r'[.!?]+\s+', answer) if len(s.strip()) > 10]
    total_claims = len(sentences)
    if total_claims == 0:
        return {"total_claims": 0, "directly_supported": 0, "reasonable_inference": 0, "general_knowledge": 0, "unsupported": 0, "hallucinated": 0}

    combined_evidence = " ".join(evidence_texts).lower()
    
    directly_supported = 0
    reasonable_inference = 0
    general_knowledge = 0
    unsupported = 0

    for sent in sentences:
        s_lower = sent.lower()
        words = set(re.findall(r'\b[a-zA-Z0-9]{4,}\b', s_lower)) - {"this", "that", "with", "from", "have", "explain", "model", "document"}
        if not words:
            general_knowledge += 1
            continue

        overlap = sum(1 for w in words if w in combined_evidence) / len(words)
        
        if overlap >= 0.35 or any(tag in sent for tag in ["[1]", "[2]", "[3]", "doc_a", "doc_b", "doc_c"]):
            directly_supported += 1
        elif not is_doc_only and overlap < 0.15:
            general_knowledge += 1
        elif is_doc_only and overlap < 0.15:
            if any(ref_phrase in s_lower for ref_phrase in ["doesn't mention", "does not contain", "not provided", "not mentioned", "couldn't find"]):
                reasonable_inference += 1
            else:
                unsupported += 1
        else:
            reasonable_inference += 1

    return {
        "total_claims": total_claims,
        "directly_supported": directly_supported,
        "reasonable_inference": reasonable_inference,
        "general_knowledge": general_knowledge,
        "unsupported": unsupported,
        "hallucinated": unsupported,
    }

def test_step2d_end_to_end_benchmark():
    print("\n==================================================")
    print("STARTING STEP 2D END-TO-END BENCHMARK")
    print("==================================================")

    engine, cfg = build_benchmark_engine()
    orchestrator = OrchestratorAgent(config=cfg, engine=engine, memory=None)

    scenarios = [
        {
            "id": "TEST_A",
            "name": "Fully Supported Document Query",
            "query": "According to doc_a_transformer_spec.txt, what is the embedding dimension and training objective of EKIP-MiniTransformer?",
            "target_doc": "doc_a_transformer_spec.txt",
        },
        {
            "id": "TEST_B",
            "name": "Partially Supported Document Query",
            "query": "Using only doc_b_encoder_spec.txt, explain the complete architecture including both the encoder and decoder modules.",
            "target_doc": "doc_b_encoder_spec.txt",
        },
        {
            "id": "TEST_C",
            "name": "Irrelevant Document Query",
            "query": "Using only doc_c_database_indexing.txt, explain the Transformer self-attention mechanism.",
            "target_doc": "doc_c_database_indexing.txt",
        },
        {
            "id": "TEST_D",
            "name": "General Knowledge Query with Unrelated Documents",
            "query": "Explain the core concepts of Transformer architectures in Machine Learning.",
            "target_doc": None,
        },
        {
            "id": "TEST_E",
            "name": "Mixed Relevant and Irrelevant Documents",
            "query": "What is the positional encoding used in EKIP-MiniTransformer according to the uploaded documents?",
            "target_doc": None,
        },
        {
            "id": "TEST_F",
            "name": "Conflicting Documents",
            "query": "How many attention heads does the EKIP-Alpha model use according to doc_conf_a.txt and doc_conf_b.txt?",
            "target_doc": None,
        },
    ]

    results = []

    for sc in scenarios:
        print(f"\n--------------------------------------------------")
        print(f"RUNNING {sc['id']}: {sc['name']}")
        print(f"Query: '{sc['query']}'")
        print(f"--------------------------------------------------")

        t0 = time.time()
        context = {
            "query": sc["query"],
            "doc_filter": [sc["target_doc"]] if sc["target_doc"] else None,
            "request_id": f"bench_{sc['id'].lower()}",
        }

        res = orchestrator.run(context)
        latency = round((time.time() - t0) * 1000, 2)

        meta = res.metadata
        sources = res.sources or []
        evidence_texts = [s.get("content", "") for s in sources]

        is_doc_only = (meta.get("planner_source_strategy") == "document_only")
        claim_eval = evaluate_claims(res.content, evidence_texts, is_doc_only)

        # Check provenance preservation
        prov_preserved = all("source_file" in s and "score" in s for s in sources) if sources else True

        sc_result = {
            "scenario_id": sc["id"],
            "scenario_name": sc["name"],
            "query": sc["query"],
            "planner_strategy": meta.get("planner_source_strategy"),
            "runtime_strategy": meta.get("runtime_source_strategy"),
            "source_mode": meta.get("source_mode"),
            "retrieved_chunks_count": meta.get("retrieved_chunks_count", 0),
            "surviving_chunks_count": len(sources),
            "rejected_chunks_count": meta.get("rejected_by_rerank_count", 0),
            "evidence_chunks": len(sources),
            "evidence_characters": sum(len(s.get("content", "")) for s in sources),
            "source_files": list(set(s.get("source_file", "Unknown") for s in sources)),
            "provenance_preserved": prov_preserved,
            "claim_evaluation": claim_eval,
            "faithfulness_score": meta.get("faithfulness", 0.0),
            "confidence": res.confidence,
            "response_latency_ms": latency,
            "provider": meta.get("provider"),
            "model": meta.get("model"),
            "content_snippet": res.content[:300] + ("..." if len(res.content) > 300 else ""),
            "full_content": res.content,
        }

        results.append(sc_result)

        print(f"Strategy: {sc_result['planner_strategy']} | Mode: {sc_result['source_mode']}")
        print(f"Sources: {sc_result['source_files']}")
        print(f"Faithfulness: {sc_result['faithfulness_score']} | Confidence: {sc_result['confidence']}%")
        print(f"Claims: {claim_eval}")

    output_path = Path(__file__).parent.parent / "scratch" / "step2d_benchmark_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n==================================================")
    print(f"STEP 2D BENCHMARK COMPLETED SUCCESSFULLY!")
    print(f"Results saved to {output_path}")
    print(f"==================================================")
    
    assert len(results) == 6
