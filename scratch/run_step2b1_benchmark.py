import time
import json
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath("."))

from dotenv import load_dotenv

load_dotenv()

from config.settings import Config
from core.planner.rules import RuleBasedPlannerEngine
from agents.synthesis import SynthesisAgent
from core.llm.manager import LLMManager
from core.llm.base_provider import BaseLLMProvider

def run_benchmark():
    planner = RuleBasedPlannerEngine()
    synthesis_agent = SynthesisAgent(Config)
    results = []

    print("==================================================", flush=True)
    print("STARTING EKIP STEP 2B.1 REAL BENCHMARK EXECUTION", flush=True)
    print("==================================================", flush=True)

    # Document mock setup for Document query
    sample_doc = {
        "content": "Enterprise AI System Architecture: Microservices architecture with FastAPI backend, ChromaDB vector store, and decoupled LLM provider registry.",
        "metadata": {"source": "ai_arch.txt"}
    }

    test_cases = [
        {
            "id": "A. Normal General Knowledge",
            "query": "Explain the core concepts of Transformer architectures in Machine Learning.",
            "docs": [sample_doc],
            "force_fail_primary": False
        },
        {
            "id": "B. Simple Query",
            "query": "What is overfitting in machine learning?",
            "docs": [],
            "force_fail_primary": False
        },
        {
            "id": "C. Another General Query",
            "query": "Explain how a database index improves query performance.",
            "docs": [],
            "force_fail_primary": False
        },
        {
            "id": "D. Strict Document Query",
            "query": "Using only my uploaded document, explain the architecture described in it.",
            "docs": [sample_doc],
            "force_fail_primary": False
        },
        {
            "id": "E. Failure/Fallback Simulation",
            "query": "Explain how distributed caching works.",
            "docs": [],
            "force_fail_primary": True
        }
    ]

    for tc in test_cases:
        print(f"\n--- Running Benchmark Case: {tc['id']} ---", flush=True)
        q = tc["query"]
        docs = tc["docs"]

        # Step 1: Planner
        t_plan0 = time.monotonic()
        plan = planner.generate_plan(
            query=q,
            available_docs=[d["metadata"]["source"] for d in docs] if docs else []
        )
        plan_dur = round((time.monotonic() - t_plan0) * 1000, 2)
        planner_strategy = plan.source_strategy.value

        # Step 2: Synthesis Execution
        context = {
            "query": q,
            "documents": docs,
            "execution_plan": plan,
            "planner_output": plan,
            "intent": "QA",
            "difficulty": "intermediate",
            "format": "detailed",
            "verified_collection": "demo_collection" if docs else ""
        }

        t_synth0 = time.monotonic()

        try:
            if tc["force_fail_primary"]:
                manager = LLMManager()
                original_select = manager.router.select_ordered_providers

                class FailingGeminiWrapper(BaseLLMProvider):
                    def __init__(self, real_provider):
                        super().__init__(real_provider.name, real_provider.primary_model, real_provider.fallback_model, real_provider.api_key)
                        self.real = real_provider

                    def get_client(self, *args, **kwargs):
                        return None

                    def generate(self, *args, **kwargs):
                        raise Exception("504 DEADLINE_EXCEEDED: Simulated primary provider timeout")

                def mock_select(intent=None):
                    providers = original_select(intent=intent)
                    res = []
                    for p in providers:
                        if p.name == "gemini":
                            res.append(FailingGeminiWrapper(p))
                        else:
                            res.append(p)
                    return res

                with patch.object(manager.router, "select_ordered_providers", side_effect=mock_select):
                    agent_res = synthesis_agent.run(context)
            else:
                agent_res = synthesis_agent.run(context)

            total_wall_clock_sec = round(time.monotonic() - t_synth0, 2)
            meta = agent_res.metadata or {}

            record = {
                "case_id": tc["id"],
                "query": q,
                "planner_strategy": planner_strategy,
                "runtime_strategy": meta.get("source_mode", "unknown"),
                "prompt_builder_used": meta.get("prompt_builder_used", True),
                "prompt_length_chars": meta.get("prompt_length_chars", 0),
                "final_provider": meta.get("provider", "NONE"),
                "final_model": meta.get("model", "none"),
                "fallback_occurred": meta.get("fallback_occurred", False),
                "fallback_chain": meta.get("fallback_chain", []),
                "total_wall_clock_duration_sec": total_wall_clock_sec,
                "response_length_chars": len(agent_res.content),
                "success": agent_res.success,
                "attempts_detail": meta.get("attempts_detail", [])
            }

            results.append(record)
            print(f"  Result: Success={record['success']} | Duration={record['total_wall_clock_duration_sec']}s | Provider={record['final_provider']} ({record['final_model']}) | Fallback={record['fallback_occurred']}", flush=True)
            if record['attempts_detail']:
                print(f"  Attempts Detail: {json.dumps(record['attempts_detail'], indent=2)}", flush=True)
        except Exception as e:
            import traceback
            print(f"  Benchmark Case {tc['id']} Exception: {e}", flush=True)
            traceback.print_exc()

    with open("scratch_step2b1_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\nBenchmark saved to scratch_step2b1_benchmark_results.json", flush=True)

if __name__ == "__main__":
    run_benchmark()
