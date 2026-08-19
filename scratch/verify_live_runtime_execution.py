"""
Verify Live Runtime Execution via app.py code path.
Prints all requested inspect values, module paths, and executes full pipeline.
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
    print("  LIVE RUNTIME INSPECTION & VERIFICATION")
    print("=" * 80)
    print(f"sys.executable                             : {sys.executable}")
    print(f"agents.orchestrator.__file__              : {getattr(agents.orchestrator, '__file__', 'N/A')}")
    print(f"OrchestratorAgent.__module__               : {OrchestratorAgent.__module__}")
    print(f"inspect.getfile(OrchestratorAgent)         : {inspect.getfile(OrchestratorAgent)}")
    print(f"inspect.getsourcefile(dispatch_sources)   : {inspect.getsourcefile(OrchestratorAgent.dispatch_selected_sources)}")
    print(f"inspect.getsourcefile(OrchestratorAgent.run): {inspect.getsourcefile(OrchestratorAgent.run)}")
    print("=" * 80)

    prompt = "Explain the core concepts of Transformer architectures in Machine Learning."
    print(f"\nEXECUTING LIVE APP.PY PIPELINE FOR: '{prompt}'\n")

    init_db()
    init_chat_db()

    engine = BaseRAGEngine(Config)
    memory = ConversationMemory(Config.OBSERVABILITY_DB)
    orch = OrchestratorAgent(Config, engine, memory)

    planning_graph = create_ekip_planning_graph()
    plan_state = planning_graph.invoke({
        "question": prompt,
        "conversation_history": [],
        "execution_mode": "chat_planning",
        "skip_synthesis": True,
    })

    exec_plan = plan_state.get("execution_plan") if isinstance(plan_state, dict) else getattr(plan_state, "execution_plan", None)
    
    prov_meta = plan_state.get("provider_metadata", {}) if isinstance(plan_state, dict) else getattr(plan_state, "provider_metadata", {})
    edu_meta = prov_meta.get("educational_response") if isinstance(prov_meta, dict) else None
    if not edu_meta:
        edu_meta = plan_state.get("educational_response") if isinstance(plan_state, dict) else getattr(plan_state, "educational_response", None)
    if hasattr(edu_meta, "dict"):
        edu_meta = edu_meta.dict()

    ctx = {
        "query": prompt,
        "history": [],
        "filters": {},
        "stream_writer": lambda chunks: "".join(list(chunks)) if isinstance(chunks, list) else str(chunks),
        "execution_plan": exec_plan,
        "educational_response": edu_meta,
        "plan_state": plan_state,
    }

    try:
        res = orch.run(ctx)
        print("\n" + "=" * 80)
        print("  LIVE RUNTIME PIPELINE EXECUTED SUCCESSFULLY")
        print("=" * 80)
        print(f"Success          : {res.success}")
        print(f"Content Length   : {len(res.content)} chars")
        print(f"Provider         : {res.metadata.get('provider', 'N/A')}")
        print(f"Model            : {res.metadata.get('model', 'N/A')}")
        print(f"Source Mode      : {res.metadata.get('source_mode', 'N/A')}")
        print(f"Confidence       : {res.confidence}%")
        print(f"Error            : {res.error}")
        print("=" * 80)
        assert res.success is True
        assert len(res.content) > 100
        assert "UnboundLocalError" not in str(res.content)
        assert res.metadata.get("provider") != "NONE"
        assert res.metadata.get("model") != "none"
        print("\nALL VERIFICATIONS PASSED ✅")
    except Exception as e:
        print("\n" + "!" * 80)
        print("  EXCEPTION AT RUNTIME:")
        print("!" * 80)
        traceback.print_exc()
        print("!" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
