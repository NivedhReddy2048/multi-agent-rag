import time
import json
from config.settings import Config
from core.engine import BaseRAGEngine
from core.memory import ConversationMemory
from agents.orchestrator import OrchestratorAgent

def run_benchmark():
    cfg = Config()
    engine = BaseRAGEngine(cfg)
    memory = ConversationMemory(":memory:")
    orchestrator = OrchestratorAgent(config=cfg, engine=engine, memory=memory)

    scenarios = [
        {
            "id": "scenario_1_general_knowledge",
            "name": "General Knowledge Query",
            "context": {
                "query": "Explain Transformer architecture in Machine Learning",
                "source_strategy": "general_knowledge",
                "request_id": "bench_s1"
            }
        },
        {
            "id": "scenario_2_doc_supported",
            "name": "DOCUMENT_ONLY Supported Query",
            "context": {
                "query": "How many attention heads does EKIP-MiniTransformer use?",
                "source_strategy": "document_only",
                "documents": [{"source_file": "doc_a.txt", "content": "EKIP-MiniTransformer uses 8 attention heads.", "score": 0.95}],
                "request_id": "bench_s2"
            }
        },
        {
            "id": "scenario_3_doc_partial",
            "name": "DOCUMENT_ONLY Partial Evidence",
            "context": {
                "query": "Explain EKIP-Encoder and EKIP-Decoder",
                "source_strategy": "document_only",
                "documents": [{"source_file": "doc_b.txt", "content": "EKIP-Encoder consists of 6 encoder blocks with self-attention.", "score": 0.88}],
                "request_id": "bench_s3"
            }
        },
        {
            "id": "scenario_4_doc_missing",
            "name": "DOCUMENT_ONLY Missing Evidence",
            "context": {
                "query": "Explain quantum computing in my document",
                "source_strategy": "document_only",
                "documents": [],
                "request_id": "bench_s4"
            }
        },
        {
            "id": "scenario_5_conflicting",
            "name": "DOCUMENT_ONLY Conflicting Evidence",
            "context": {
                "query": "How many attention heads does EKIP-Alpha use?",
                "source_strategy": "document_only",
                "documents": [
                    {"source_file": "doc_conf_a.txt", "content": "EKIP-Alpha uses 8 attention heads.", "score": 0.90},
                    {"source_file": "doc_conf_b.txt", "content": "EKIP-Alpha uses 12 attention heads.", "score": 0.85}
                ],
                "request_id": "bench_s5"
            }
        },
        {
            "id": "scenario_6_citations",
            "name": "Citation Anchoring Validation",
            "context": {
                "query": "What is the layer count of EKIP-MiniTransformer?",
                "source_strategy": "document_only",
                "documents": [{"source_file": "doc_a.txt", "content": "EKIP-MiniTransformer features 12 transformer layers.", "score": 0.92}],
                "request_id": "bench_s6"
            }
        }
    ]

    results = []
    print("=" * 80)
    print("  EKIP STEP 2E END-TO-END BENCHMARK EXECUTION")
    print("=" * 80)

    for sc in scenarios:
        t0 = time.time()
        print(f"\nRunning {sc['id']}: {sc['name']}...")
        res = orchestrator.run(sc["context"])
        dt = time.time() - t0

        out = {
            "id": sc["id"],
            "name": sc["name"],
            "duration_sec": round(dt, 2),
            "content_snippet": res.content[:300] + "..." if len(res.content) > 300 else res.content,
            "faithfulness": res.metadata.get("faithfulness"),
            "faithfulness_applicable": res.metadata.get("faithfulness_applicable"),
            "faithfulness_reason": res.metadata.get("faithfulness_reason"),
            "warnings": res.metadata.get("warnings", []),
            "sources_count": len(res.sources),
        }
        results.append(out)
        print(f"  Duration: {out['duration_sec']}s")
        print(f"  Faithfulness: {out['faithfulness']} (Applicable: {out['faithfulness_applicable']}, Reason: {out['faithfulness_reason']})")
        print(f"  Warnings: {out['warnings']}")
        print(f"  Response Snippet:\n{out['content_snippet']}\n")

    print("=" * 80)
    print("  BENCHMARK SUMMARY")
    print("=" * 80)
    for r in results:
        print(f"{r['id']:<30} | Dur: {r['duration_sec']}s | Faithfulness: {r['faithfulness']} | Applicable: {r['faithfulness_applicable']}")

if __name__ == "__main__":
    import sys
    import traceback
    try:
        run_benchmark()
    except Exception as e:
        print(f"BENCHMARK ERROR: {e}", flush=True)
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()

