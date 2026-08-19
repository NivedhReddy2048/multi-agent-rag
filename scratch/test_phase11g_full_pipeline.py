"""
EKIP Phase 11G — Comprehensive Dual Verification Test.
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath("."))

from config.settings import Config
from core.auth.database import init_db
from core.chat.database import init_chat_db
from core.engine import BaseRAGEngine
from core.memory import ConversationMemory
from agents.orchestrator import OrchestratorAgent
from graph.builder import create_ekip_planning_graph


def run_test_query(prompt: str, orch: OrchestratorAgent):
    print("\n" + "=" * 70)
    print(f"  TESTING QUERY: '{prompt}'")
    print("=" * 70)

    t0 = time.time()
    planning_graph = create_ekip_planning_graph()
    plan_state = planning_graph.invoke({
        "question": prompt,
        "conversation_history": [],
        "execution_mode": "chat_planning",
        "skip_synthesis": True,
    })
    exec_plan = plan_state.get("execution_plan") if isinstance(plan_state, dict) else getattr(plan_state, "execution_plan", None)
    print(f"  Planner Intent  : {getattr(exec_plan, 'intent', None)}")
    print(f"  Planner Strategy: {getattr(exec_plan, 'source_strategy', None)}")
    print(f"  Doc Usage Mode  : {getattr(exec_plan, 'document_usage_mode', None)}")

    edu_meta = (plan_state.get("provider_metadata", {}) if isinstance(plan_state, dict) else getattr(plan_state, "provider_metadata", {})).get("educational_response") or (plan_state.get("educational_response") if isinstance(plan_state, dict) else getattr(plan_state, "educational_response", None))
    if hasattr(edu_meta, "dict"):
        edu_meta = edu_meta.dict()

    ctx = {
        "query": prompt,
        "history": [],
        "filters": {},
        "stream_writer": lambda chunk: None,
        "execution_plan": exec_plan,
        "educational_response": edu_meta,
        "plan_state": plan_state,
    }

    result = orch.run(ctx)
    latency_ms = int((time.time() - t0) * 1000)

    print("\n--- RESULT ---")
    print(f"Success          : {result.success}")
    print(f"Content Length   : {len(result.content)} chars")
    print(f"Provider         : {result.metadata.get('provider')}")
    print(f"Model            : {result.metadata.get('model')}")
    print(f"Source Mode      : {result.metadata.get('source_mode')}")
    print(f"Confidence       : {result.confidence}%")
    print(f"Total Latency    : {latency_ms} ms")
    print(f"Error            : '{result.error}'")
    assert result.success, f"Execution failed for query: {prompt}"
    assert len(result.content) > 100, f"Content too short for query: {prompt}"
    print("STATUS: PASS ✅")


def main():
    init_db()
    init_chat_db()

    print("Initializing Engine, Memory, and Orchestrator...")
    engine = BaseRAGEngine(Config)
    memory = ConversationMemory(Config.OBSERVABILITY_DB)
    orch = OrchestratorAgent(Config, engine, memory)

    run_test_query("Explain the core concepts of Transformer architectures in Machine Learning.", orch)
    run_test_query("Summarize my uploaded cover letter document", orch)


if __name__ == "__main__":
    main()
