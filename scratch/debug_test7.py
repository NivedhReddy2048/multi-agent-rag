import sys, os
sys.path.insert(0, os.path.abspath("."))
from config.settings import Config
from core.auth.database import init_db
from core.chat.database import init_chat_db
from core.engine import BaseRAGEngine
from core.memory import ConversationMemory
from graph.builder import create_ekip_planning_graph
from agents.orchestrator import OrchestratorAgent
from core.llm.manager import LLMManager

init_db()
init_chat_db()

# Force provider timeout
original_generate = LLMManager.generate
def fast_generate(self, *args, **kwargs):
    kwargs["timeout"] = 0.1
    return original_generate(self, *args, **kwargs)
LLMManager.generate = fast_generate

engine = BaseRAGEngine(Config)
memory = ConversationMemory(Config.OBSERVABILITY_DB)
orch = OrchestratorAgent(Config, engine, memory)
planning_graph = create_ekip_planning_graph()

query = "Generate a 5-question quiz on Python OOP."
plan_state = planning_graph.invoke({
    "question": query,
    "conversation_history": [],
    "execution_mode": "chat_planning",
    "skip_synthesis": True,
})
exec_plan = plan_state.get("execution_plan") if isinstance(plan_state, dict) else getattr(plan_state, "execution_plan", None)

ctx = {
    "query": query,
    "history": [],
    "filters": {},
    "execution_plan": exec_plan,
    "plan_state": plan_state,
}
res = orch.run(ctx)

with open("scratch/debug_output.txt", "w", encoding="utf-8") as f:
    f.write("--- DEBUG TEST 7 RESULT ---\n")
    f.write(f"Content: {repr(res.content)}\n")
    f.write(f"Confidence: {res.confidence}\n")
    f.write(f"Sources count: {len(res.sources)}\n")
    f.write(f"Metadata: {res.metadata}\n")

