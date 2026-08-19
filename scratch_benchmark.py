"""Scratch script for Step 2B End-to-End Baseline Benchmark Evaluation."""

import sys
import time
import json
import os
from config.settings import Config
from agents.orchestrator import OrchestratorAgent
from core.engine import BaseRAGEngine

def run_benchmark():
    print("=" * 60)
    print("STARTING EKIP STEP 2B END-TO-END BENCHMARK EVALUATION")
    print("=" * 60)

    # Initialize Engine & Orchestrator
    engine = BaseRAGEngine.get_instance()
    memory = None
    orchestrator = OrchestratorAgent(Config, engine, memory)

    queries = [
        ("TEST A", "Explain the core concepts of Transformer architectures in Machine Learning."),
        ("TEST B", "Explain how a database index improves query performance."),
        ("TEST C", "What is overfitting in machine learning?"),
        ("TEST D", "Using only my uploaded document, explain the architecture described in it."),
        ("TEST E", "Explain quantum computing."),
    ]

    results = []

    for test_id, query in queries:
        print(f"\n------------------------------------------------------------")
        print(f"RUNNING {test_id}: '{query}'")
        print(f"------------------------------------------------------------")

        t0 = time.time()
        context = {
            "query": query,
            "history": [],
            "user_id": "eval_user",
            "session_id": "eval_session",
        }

        try:
            res = orchestrator.run(context)
            duration_ms = round((time.time() - t0) * 1000, 2)

            meta = res.metadata or {}
            content = res.content or ""

            prompt_used = ""
            if os.path.exists("debug/final_prompt.txt"):
                with open("debug/final_prompt.txt", "r", encoding="utf-8") as f:
                    prompt_used = f.read()

            prompt_builder_invoked = "PEDAGOGICAL & EXPLANATION FRAMEWORK:" in prompt_used or "EducationalPromptBuilder" in str(res.agent_trace)

            info = {
                "test_id": test_id,
                "query": query,
                "success": res.success,
                "content_len": len(content),
                "duration_ms": duration_ms,
                "planner_strategy": meta.get("planner_strategy", meta.get("source_strategy", "N/A")),
                "runtime_strategy": meta.get("runtime_strategy", meta.get("source_mode", "N/A")),
                "doc_retrieval_executed": meta.get("doc_retrieval_executed", False),
                "web_retrieval_executed": meta.get("web_retrieval_executed", False),
                "prompt_builder_invoked": prompt_builder_invoked,
                "provider": meta.get("provider", "Unknown"),
                "model": meta.get("model", "Unknown"),
                "fallback_occurred": meta.get("fallback_occurred", False),
                "fallback_chain": meta.get("fallback_chain", []),
                "error": res.error or meta.get("error", ""),
                "agent_trace": res.agent_trace,
                "content_preview": content[:600] + ("..." if len(content) > 600 else ""),
                "full_content": content,
            }

            print(f"Provider: {info['provider']} | Model: {info['model']} | Duration: {duration_ms}ms | Len: {info['content_len']}")
            print(f"Planner Strat: {info['planner_strategy']} | Runtime Strat: {info['runtime_strategy']}")
            print(f"Docs Executed: {info['doc_retrieval_executed']} | Web Executed: {info['web_retrieval_executed']}")
            print(f"Prompt Builder Invoked: {info['prompt_builder_invoked']}")
            print("\nPreview:\n" + info["content_preview"] + "\n")

            results.append(info)

        except Exception as e:
            print(f"ERROR executing {test_id}: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "test_id": test_id,
                "query": query,
                "success": False,
                "error": str(e),
                "duration_ms": round((time.time() - t0) * 1000, 2),
            })

    with open("scratch_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\nBENCHMARK RUN COMPLETE. Results saved to scratch_benchmark_results.json")

if __name__ == "__main__":
    run_benchmark()
