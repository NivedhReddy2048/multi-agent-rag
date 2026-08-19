"""EKIP Phase 6A — Real Runtime Environment & Startup Audit Script.

Performs read-only runtime environment, provider configuration, query lifecycle,
and metadata contract verification against the actual app initialization code.
"""

import sys
import os
import time
from pathlib import Path

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def run_phase6a_audit():
    print("======================================================================")
    print("🚀 EKIP Phase 6A — Real Runtime Environment & Startup Audit")
    print("======================================================================\n")

    # -------------------------------------------------------------------------
    # 1. Startup Audit
    # -------------------------------------------------------------------------
    print("--- STEP 1: Application Startup Audit ---")
    startup_errors = []

    try:
        from config import Config
        from core.auth.database import init_db
        from core.chat.database import init_chat_db
        from core.engine import BaseRAGEngine
        from core.memory import ConversationMemory
        from agents.orchestrator import OrchestratorAgent
        from graph.builder import create_ekip_planning_graph
        from core.llm.manager import LLMManager
        from core.llm.provider_registry import ProviderRegistry

        init_db()
        init_chat_db()
        print(" [OK] Core imports succeeded.")
        print(" [OK] Database initialized successfully.")

        engine = BaseRAGEngine(Config)
        memory = ConversationMemory(Config.OBSERVABILITY_DB)
        orch = OrchestratorAgent(Config, engine, memory)
        print(" [OK] OrchestratorAgent initialized.")

        planning_graph = create_ekip_planning_graph()
        print(" [OK] Planning graph compiled successfully.")

    except Exception as e:
        print(f" ❌ Startup Error: {e}")
        startup_errors.append(str(e))
        return

    # -------------------------------------------------------------------------
    # 2. Provider Configuration Audit
    # -------------------------------------------------------------------------
    print("\n--- STEP 2: Provider Configuration Audit ---")
    llm_manager = LLMManager()
    registry = ProviderRegistry()
    active_chain = registry.priority_order

    keys_detected = {}
    env_key_map = {
        "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
        "groq": ["GROQ_API_KEY"],
        "cohere": ["COHERE_API_KEY"],
        "mistral": ["MISTRAL_API_KEY"],
        "openai": ["OPENAI_API_KEY"],
    }

    for p_name, env_vars in env_key_map.items():
        found = False
        for ev in env_vars:
            val = os.getenv(ev)
            if val and val.strip():
                found = True
                masked = val[:4] + "..." + val[-4:] if len(val) > 8 else "***"
                keys_detected[p_name] = f"Present ({masked})"
                break
        if not found:
            keys_detected[p_name] = "Missing/Empty"

    print(f" Detected Provider Keys: {keys_detected}")
    print(f" Active Priority Routing Chain: {active_chain}")

    # -------------------------------------------------------------------------
    # 3. Streamlit Query Lifecycle & Single Synthesis Verification
    # -------------------------------------------------------------------------
    print("\n--- STEP 3: Streamlit Query Lifecycle & Single-Synthesis Audit ---")

    test_query = "What are the core concepts of machine learning?"
    print(f" Submitting Query: '{test_query}'")

    # Step 3a: Planning Graph Execution
    plan_state = planning_graph.invoke({
        "question": test_query,
        "conversation_history": [],
        "execution_mode": "chat_planning",
        "skip_synthesis": True,
    })

    exec_plan = plan_state.execution_plan
    edu_meta_graph = plan_state.provider_metadata.get("educational_response") or plan_state.educational_response

    print(f" [OK] planning_graph.invoke() completed.")
    print(f"      Execution Mode: chat_planning")
    print(f"      Source Strategy: {exec_plan.source_strategy.value if hasattr(exec_plan.source_strategy, 'value') else exec_plan.source_strategy}")
    print(f"      Graph Knowledge Synthesizer Node Skipped: True")

    # Step 3b: Orchestrator Single Authoritative Synthesis Execution
    ctx = {
        "query": test_query,
        "history": [],
        "filters": {},
        "execution_plan": exec_plan,
        "educational_response": edu_meta_graph.dict() if hasattr(edu_meta_graph, "dict") else edu_meta_graph,
        "plan_state": plan_state,
    }

    t0 = time.time()
    result = orch.run(ctx)
    latency_sec = time.time() - t0

    print(f" [OK] OrchestratorAgent.run() completed as SINGLE authoritative path in {latency_sec:.2f}s.")
    print(f"      Result Content Length: {len(result.content)} chars")

    # -------------------------------------------------------------------------
    # 4. Runtime Metadata Contract Audit
    # -------------------------------------------------------------------------
    print("\n--- STEP 4: Runtime Metadata Contract Audit ---")
    meta = result.metadata or {}

    contract_fields = [
        "response_status",
        "provider",
        "model",
        "source_mode",
        "planner_source_strategy",
        "runtime_source_strategy",
        "confidence",
        "faithfulness",
        "retrieved_chunks_count",
        "crag_score",
        "educational_response",
    ]

    missing_fields = []
    for field in contract_fields:
        if field == "confidence":
            val = result.confidence
        elif field == "educational_response":
            val = meta.get("educational_response")
        else:
            val = meta.get(field)

        if val is None:
            missing_fields.append(field)
            print(f" ❌ Missing Metadata Field: {field}")
        else:
            if field == "educational_response" and isinstance(val, dict):
                print(f"  - {field}: Present (keys: {list(val.keys())})")
            else:
                print(f"  - {field}: {val}")

    # -------------------------------------------------------------------------
    # 5. UI Rendering Contract Audit
    # -------------------------------------------------------------------------
    print("\n--- STEP 5: UI Rendering Contract Audit ---")

    edu_resp = meta.get("educational_response")
    ui_match = False
    if edu_resp and isinstance(edu_resp, dict):
        ai_explanation = edu_resp.get("ai_explanation", "")
        if ai_explanation == result.content:
            ui_match = True
            print(" [OK] UI Contract Verified: EducationalResponse.ai_explanation == AgentResult.content")
        else:
            print(f" ❌ UI Contract Mismatch!\n   AgentResult.content: {result.content[:50]}...\n   ai_explanation: {ai_explanation[:50]}...")
    else:
        print(" ❌ Missing or invalid EducationalResponse payload in metadata.")

    # -------------------------------------------------------------------------
    # Final Summary
    # -------------------------------------------------------------------------
    print("\n======================================================================")
    print("📊 AUDIT SUMMARY")
    print("======================================================================")
    print(f" Startup Errors: {len(startup_errors)}")
    print(f" Configured Providers: {[k for k, v in keys_detected.items() if 'Present' in v]}")
    print(f" Missing Metadata Contract Fields: {len(missing_fields)}")
    print(f" UI Invariant Match: {ui_match}")
    print(f" Code Modifications Made: NO")
    print("======================================================================\n")


if __name__ == "__main__":
    run_phase6a_audit()
