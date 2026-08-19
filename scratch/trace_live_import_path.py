"""
Live runtime investigation: Print import paths, source file locations, and capture exact traceback.
"""

import sys
import os
import inspect
import traceback

sys.path.insert(0, os.path.abspath("."))

import agents.orchestrator
from agents.orchestrator import OrchestratorAgent
from config.settings import Config
from core.auth.database import init_db
from core.chat.database import init_chat_db
from core.engine import BaseRAGEngine
from core.memory import ConversationMemory
from graph.builder import create_ekip_planning_graph


def main():
    print("=" * 80)
    print("  LIVE RUNTIME IMPORT & MODULE DIAGNOSTICS")
    print("=" * 80)

    print(f"sys.executable                             : {sys.executable}")
    print(f"sys.path[0]                                : {sys.path[0]}")
    print(f"agents.orchestrator.__file__              : {getattr(agents.orchestrator, '__file__', 'N/A')}")
    print(f"OrchestratorAgent.__module__               : {OrchestratorAgent.__module__}")
    print(f"inspect.getfile(OrchestratorAgent)         : {inspect.getfile(OrchestratorAgent)}")
    print(f"OrchestratorAgent.dispatch_selected_sources: {inspect.getsourcefile(OrchestratorAgent.dispatch_selected_sources)}")
    print(f"OrchestratorAgent.run                      : {inspect.getsourcefile(OrchestratorAgent.run)}")
    print("=" * 80)

    # Now let's run the exact query that failed in UI
    query = "Explain the core concepts of Transformer architectures in Machine Learning."
    print(f"\nREPRODUCING LIVE QUERY: '{query}'\n")

    init_db()
    init_chat_db()

    engine = BaseRAGEngine(Config)
    memory = ConversationMemory(Config.OBSERVABILITY_DB)
    orch = OrchestratorAgent(Config, engine, memory)

    planning_graph = create_ekip_planning_graph()
    plan_state = planning_graph.invoke({
        "question": query,
        "conversation_history": [],
        "execution_mode": "chat_planning",
        "skip_synthesis": True,
    })
    exec_plan = plan_state.get("execution_plan") if isinstance(plan_state, dict) else getattr(plan_state, "execution_plan", None)

    edu_meta = (plan_state.get("provider_metadata", {}) if isinstance(plan_state, dict) else getattr(plan_state, "provider_metadata", {})).get("educational_response") or (plan_state.get("educational_response") if isinstance(plan_state, dict) else getattr(plan_state, "educational_response", None))
    if hasattr(edu_meta, "dict"):
        edu_meta = edu_meta.dict()

    ctx = {
        "query": query,
        "history": [],
        "filters": {},
        "stream_writer": lambda chunk: None,
        "execution_plan": exec_plan,
        "educational_response": edu_meta,
        "plan_state": plan_state,
    }

    try:
        res = orch.run(ctx)
        print("\n--- EXECUTION SUCCESSFUL ---")
        print(f"Result Content Length: {len(res.content)}")
        print(f"Result Metadata      : {res.metadata}")
    except Exception as e:
        print("\n" + "!" * 80)
        print("  EXACT FULL TRACEBACK CAPTURED:")
        print("!" * 80)
        traceback.print_exc()
        print("!" * 80)


if __name__ == "__main__":
    main()
