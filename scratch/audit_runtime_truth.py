import sys
import os
import time
import json
from dataclasses import asdict

# Ensure project root is in path
sys.path.insert(0, r"d:\MultiAgentRAG-3")

from config.settings import Config
from core.engine import BaseRAGEngine
from core.memory import ConversationMemory
from agents.orchestrator import OrchestratorAgent
from agents.base import AgentResult
from core.llm.manager import LLMManager

def run_truth_audit():
    print("=" * 80)
    print("      EKIP RUNTIME TRUTH AUDIT — NO ASSUMPTIONS EXECUTION")
    print("=" * 80)

    # 1. Initialize Core Components
    engine = BaseRAGEngine(Config)
    memory = ConversationMemory(Config.OBSERVABILITY_DB)
    orch = OrchestratorAgent(Config, engine, memory)

    # 2. Construct Query Context simulating app.py
    query = "What is LangChain architecture?"
    cid = memory.create_conversation("Audit Test Session")

    # Captured stream chunks
    captured_stream_chunks = []
    def mock_stream_writer(generator):
        chunks = []
        for chunk in generator:
            print(f"[STREAM YIELD CHUNK] repr: {repr(chunk)} | len: {len(chunk)}")
            chunks.append(chunk)
            captured_stream_chunks.append(chunk)
        return "".join(chunks)

    ctx = {
        "query": query,
        "history": [],
        "filters": {},
        "stream_writer": mock_stream_writer
    }

    print("\n--- TASK 1: EXECUTING ORCHESTRATOR.RUN ---")
    t0 = time.time()
    result = orch.run(ctx)
    elapsed = time.time() - t0

    print("\n" + "=" * 80)
    print("=== TASK 11: RUNTIME VARIABLE SNAPSHOT ===")
    print("=" * 80)
    print(f"Elapsed Time       : {elapsed:.2f}s")
    print(f"Result Type        : {type(result)}")
    print(f"Result Content Len : {len(result.content)}")
    print(f"Result Content Repr: {repr(result.content[:150])}...")
    print(f"Confidence Score   : {result.confidence}")
    print(f"Sources Count      : {len(result.sources)}")
    print(f"Agent Trace        : {[str(t).encode('ascii', 'replace').decode('ascii') for t in result.agent_trace]}")
    print(f"Metadata Object    : {json.dumps(result.metadata, indent=2)}")

    # 3. Assertions (TASK 12)
    print("\n--- RUNNING TASK 12 ASSERTIONS ---")
    assert result.content != "", "FAIL: result.content is empty"
    assert "RESOURCE_EXHAUSTED" not in result.content, "FAIL: Raw 429 RESOURCE_EXHAUSTED leaked to content"
    assert "429" not in result.content, "FAIL: Raw 429 error code leaked to content"
    assert result.metadata["provider"] != "UNKNOWN", "FAIL: Provider is UNKNOWN"
    assert result.metadata["model"] != "Unknown", "FAIL: Model is Unknown"
    assert isinstance(result.metadata, dict), "FAIL: metadata is not a dict"
    assert result.content != str(result.metadata), "FAIL: content equals str(metadata)"
    print("[SUCCESS] ALL TASK 12 ASSERTIONS PASSED!")

    # 4. Persistence Test (TASK 9 / TASK 10)
    print("\n--- TESTING MEMORY PERSISTENCE & RELOAD ---")
    memory.add_message(cid, "user", query)
    memory.add_message(
        cid,
        "assistant",
        result.content,
        agent_trace=result.agent_trace,
        citations=result.sources,
        confidence=result.confidence,
        latency_ms=int(elapsed * 1000),
        metadata=result.metadata
    )

    reloaded_messages = memory.get_messages(cid)
    print(f"Reloaded Messages Count: {len(reloaded_messages)}")
    for i, msg in enumerate(reloaded_messages):
        print(f"  Msg #{i} Role: {msg['role']} | Metadata: {msg.get('metadata')}")

    last_assistant_msg = [m for m in reloaded_messages if m["role"] == "assistant"][-1]
    assert last_assistant_msg["metadata"]["provider"] == result.metadata["provider"], "FAIL: Provider did not persist in SQLite"
    print("[SUCCESS] MEMORY PERSISTENCE VERIFIED SUCCESSFUL!")

if __name__ == "__main__":
    run_truth_audit()
