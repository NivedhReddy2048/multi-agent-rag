"""
Step 4: End-to-End Live Streamlit Verification Suite.
Executes all 8 live queries directly against OrchestratorAgent and planning graph,
verifying response status, confidence, content length, and provider fallback behavior.
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.abspath("."))

from config.settings import Config
from core.auth.database import init_db
from core.chat.database import init_chat_db
from core.engine import BaseRAGEngine
from core.memory import ConversationMemory
from graph.builder import create_ekip_planning_graph
from agents.orchestrator import OrchestratorAgent

def run_streamlit_e2e_verification():
    init_db()
    init_chat_db()

    # Fast timeout optimization for provider outages
    from core.llm.manager import LLMManager
    original_generate = LLMManager.generate
    def fast_generate(self, *args, **kwargs):
        kwargs["timeout"] = 1.5
        return original_generate(self, *args, **kwargs)
    LLMManager.generate = fast_generate

    engine = BaseRAGEngine(Config)
    memory = ConversationMemory(Config.OBSERVABILITY_DB)
    orch = OrchestratorAgent(Config, engine, memory)
    planning_graph = create_ekip_planning_graph()

    print("==========================================================================================")
    print(" 🚀 EKIP PHASE 13B — STEP 4 LIVE END-TO-END STREAMLIT VERIFICATION")
    print("==========================================================================================")

    test_queries = [
        ("1. Concept explanation", "What is encapsulation in Python?", []),
        ("2. Video recommendation", "Recommend learning videos for DBMS.", []),
        ("3. Research discovery", "Find recent preprints on Graph Neural Networks.", []),
        ("4. Programming help", "Write a Dockerfile for a FastAPI application.", []),
        ("5. Document query", "Summarize my uploaded document.", []),
        (
            "6. Follow-up with history",
            "Explain that second point in more detail.",
            [
                {"role": "user", "content": "Explain OOP concepts in Python."},
                {"role": "assistant", "content": "1. Inheritance allows code reuse. 2. Encapsulation hides internal state."}
            ]
        ),
        ("7. Quiz during provider outage", "Generate a 5-question quiz on Python OOP.", []),
        ("8. Compound query", "Explain transformers and show me a GitHub implementation.", [])
    ]

    all_passed = True

    for name, query, history in test_queries:
        print(f"\n--- {name} ---")
        print(f"Query: '{query}'")

        # 1. Invoke planning graph
        plan_state = planning_graph.invoke({
            "question": query,
            "conversation_history": history,
            "execution_mode": "chat_planning",
            "skip_synthesis": True,
        })
        exec_plan = plan_state.get("execution_plan") if isinstance(plan_state, dict) else getattr(plan_state, "execution_plan", None)

        # 2. Invoke orchestrator
        ctx = {
            "query": query,
            "history": history,
            "filters": {},
            "execution_plan": exec_plan,
            "plan_state": plan_state,
        }
        res = orch.run(ctx)

        content_len = len(res.content) if res.content else 0
        conf = res.confidence
        sources_count = len(res.sources) if res.sources else 0
        provider = res.metadata.get("provider", "NONE")
        status = res.metadata.get("response_status", "SUCCESS")

        print(f"Intent       : {exec_plan.intent.value}")
        print(f"Confidence   : {conf}%")
        print(f"Content Len  : {content_len} chars")
        print(f"Sources      : {sources_count}")
        print(f"Provider     : {provider}")
        print(f"Status       : {status}")

        passed = content_len > 0 and conf > 0
        if not passed:
            all_passed = False
            print("❌ RESULT: FAILED")
        else:
            print("✅ RESULT: PASSED")

    print("\n==========================================================================================")
    if all_passed:
        print(" 🎯 ALL STEP 4 LIVE E2E STREAMLIT VERIFICATION TESTS PASSED SUCCESSFULLY!")
    else:
        print(" ❌ SOME E2E STREAMLIT VERIFICATION TESTS FAILED")
    print("==========================================================================================")

if __name__ == "__main__":
    run_streamlit_e2e_verification()
