"""
EKIP Phase 11G — Orchestrator Execution Exception Tracer.
Executes exact app.py pipeline for query:
"Explain the core concepts of Transformer architectures in Machine Learning."
and prints full traceback when an exception occurs.
"""

import sys
import os
import time
import traceback

sys.path.insert(0, os.path.abspath("."))

from config.settings import Config
from core.engine import BaseRAGEngine
from core.memory import ConversationMemory
from agents.orchestrator import OrchestratorAgent
from graph.builder import create_ekip_planning_graph


from core.auth.database import init_db
from core.chat.database import init_chat_db


def main():
    init_db()
    init_chat_db()
    print("=" * 70)
    print("  EKIP PHASE 11G — ORCHESTRATOR EXCEPTION TRACER")
    print("=" * 70)

    prompt = "Explain the core concepts of Transformer architectures in Machine Learning."
    print(f"\n1. Executing query: '{prompt}'")

    engine = BaseRAGEngine(Config)
    memory = ConversationMemory(Config.OBSERVABILITY_DB)
    orch = OrchestratorAgent(Config, engine, memory)

    # Step 1: LangGraph planning
    print("\n2. Invoking planning_graph...")
    planning_graph = create_ekip_planning_graph()
    plan_state = planning_graph.invoke({
        "question": prompt,
        "conversation_history": [],
        "execution_mode": "chat_planning",
        "skip_synthesis": True,
    })
    exec_plan = plan_state.execution_plan
    edu_meta = plan_state.provider_metadata.get("educational_response") or plan_state.educational_response
    if hasattr(edu_meta, "dict"):
        edu_meta = edu_meta.dict()

    print(f"Plan Intent: {plan_state.intent}")
    print(f"Plan Strategy: {plan_state.strategy}")

    # Step 2: Construct ctx
    ctx = {
        "query": prompt,
        "history": [],
        "filters": {},
        "stream_writer": lambda chunk: None,
        "execution_plan": exec_plan,
        "educational_response": edu_meta,
        "plan_state": plan_state,
    }

    # Step 3: Run Orchestrator
    print("\n3. Executing orch.run(ctx)...")
    try:
        result = orch.run(ctx)
        print("\n[SUCCESS] Orchestrator executed cleanly!")
        print(f"Content length: {len(result.content)} chars")
        print(f"Metadata      : {result.metadata}")
    except Exception as e:
        print(f"\n[EXCEPTION CAUGHT] {type(e).__name__}: {e}")
        print("\n--- FULL TRACEBACK ---")
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except Exception as top_e:
        print(f"TOP-LEVEL EXCEPTION: {top_e}", flush=True)
        traceback.print_exc()

