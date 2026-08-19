import sys
import os
import json
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import Config
from core.auth.database import init_db
from core.chat.database import init_chat_db
init_db()
init_chat_db()

from core.engine import BaseRAGEngine
from agents.orchestrator import OrchestratorAgent
from graph.builder import create_ekip_graph
from core.memory import ConversationMemory

engine = BaseRAGEngine(Config)
memory = ConversationMemory("./data/chat_history.db")
orchestrator = OrchestratorAgent(Config, engine, memory)
planning_graph = create_ekip_graph()

query = "Summarize the architecture configuration from ai_architecture.txt and the server hardware from hardware_specs.txt."
docs = ["ai_architecture.txt", "hardware_specs.txt"]

print("--- Step 1: Planning Graph ---")
plan_state = planning_graph.invoke({
    "user_query": query,
    "user_id": "acceptance_test_user",
    "selected_docs": docs,
    "execution_mode": "chat_planning",
    "skip_synthesis": True,
})
exec_plan = plan_state.get("execution_plan")
print("Exec Plan strategy:", getattr(exec_plan, "source_strategy", None))
print("Exec Plan target_docs:", getattr(exec_plan, "target_documents", None))
print("Exec Plan req internal docs:", getattr(exec_plan, "requires_internal_documents", None))

print("\n--- Step 2: Orchestrator ---")
ctx = {
    "query": query,
    "execution_plan": exec_plan,
    "intent": plan_state.get("intent"),
    "difficulty": plan_state.get("difficulty"),
    "source_strategy": plan_state.get("source_strategy"),
    "filters": {"doc_filter": docs},
    "history": [],
}
res = orchestrator.run(ctx)
print("Response Status:", res.metadata.get("response_status"))
print("Sources Count:", len(res.sources))
for s in res.sources:
    print("  - Chunk from:", s.get("source_file"), "Content:", s.get("content")[:80])
