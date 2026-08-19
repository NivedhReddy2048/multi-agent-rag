import sys
import os
sys.path.insert(0, os.path.abspath("."))
from typing import Dict, Any, List
from langchain_core.documents import Document

from config.settings import Config
from core.planner.rules import RuleBasedPlannerEngine
from agents.orchestrator import OrchestratorAgent
from core.synthesis.agent_response_adapter import agent_response_adapter
from core.memory import ConversationMemory
from core.llm_manager import LLMManager
from core.llm.base_provider import LLMResponse
from agents.synthesis import SynthesisAgent
from agents.base import AgentResult

def mock_llm_generate(self, prompt_or_chain_fn, inputs=None, **kwargs):
    query = kwargs.get("query") or "Topic Explanation"
    mock_content = (
        f"### Synthesis for: '{query}'\n\n"
        f"Retrieval-Augmented Generation provides structured evidence grounding [1].\n"
    )
    return LLMResponse(
        provider="mock_groq",
        model="gpt-oss-20b",
        content=mock_content,
        latency=10.0,
        tokens=150,
        success=True,
        error="",
        fallback_occurred=False,
        fallback_chain=["mock_groq"],
        prompt_tokens=80,
        completion_tokens=70,
        attempts_detail=[],
        prompt_builder_used=True,
        prompt_length_chars=len(mock_content)
    )

LLMManager.generate = mock_llm_generate

def _bulletproof_synth_run(self, context):
    query = context.get("query", "")
    docs = context.get("documents", [])
    source_mode = context.get("source_mode", "web")
    
    mock_content = f"### Educational Answer for: {query}\n\nEvidence grounded response [1]."
    return AgentResult(
        content=mock_content,
        confidence=85,
        sources=docs,
        agent_trace=["Generated synthesized response via bulletproof audit synthesis engine"],
        metadata={
            "latency_ms": 15,
            "intent": "QA",
            "provider": "mock_groq",
            "model": "gpt-oss-20b",
            "fallback_occurred": False,
            "fallback_chain": ["mock_groq"],
            "tokens": 250,
            "error": "",
            "failure_reason": "",
            "success": True,
            "source_mode": source_mode,
        },
        success=True
    )

SynthesisAgent.run = _bulletproof_synth_run


class MockRAGEngineWithDocs:
    """Mock engine containing indexed document with embedding dimension."""
    def __init__(self, cfg):
        self.cfg = cfg

    def dense_search(self, query, k=8, doc_filter=None):
        if "battery" in query.lower():
            return []
        return [
            Document(
                page_content="Embedding dimension: 768. Model configuration parameter dimension size is 768.",
                metadata={"source_file": "Vector_DB_Docs.pdf", "page_number": 1, "chunk_id": "vec_chunk_1"}
            )
        ]

    def sparse_search(self, query, k=8, doc_filter=None):
        return self.dense_search(query, k, doc_filter)

    def reciprocal_rank_fusion(self, dense, sparse):
        return dense

    def rerank(self, query, fused, top_k=6, min_score_override=None):
        if not fused:
            return []
        for d in fused:
            d.metadata["score"] = 5.2
        return [(d, 5.2) for d in fused]

    def compress_context(self, reranked, max_chunks=6):
        return [d for d, _ in reranked]

    def confidence(self):
        return 85

    def list_docs(self):
        return {"Vector_DB_Docs.pdf": {"chunks": 10, "pages": 5, "uploaded": "2026-08-18", "size_mb": 1.2}}


def test_phase8b_scenarios():
    print("=" * 80)
    print("EKIP PHASE 8B — VERIFICATION SUITE")
    print("=" * 80)

    cfg = Config()
    engine = MockRAGEngineWithDocs(cfg)
    memory = ConversationMemory(":memory:")
    orch = OrchestratorAgent(cfg, engine, memory)

    # -------------------------------------------------------------------------
    # TEST 1: Strict Document Success
    # -------------------------------------------------------------------------
    print("\n--- [TEST 1] Strict Document Success ---")
    q1 = "According to my uploaded document, what is the embedding dimension?"
    plan1 = RuleBasedPlannerEngine.generate_plan(q1, available_docs=["Vector_DB_Docs.pdf"])
    res1 = orch.run({"query": q1, "execution_plan": plan1, "doc_filter": ["Vector_DB_Docs.pdf"]})
    edu1 = agent_response_adapter.compose_from_agent_result(res1)
    
    print(f"  Strategy      : {plan1.source_strategy.value}")
    print(f"  Response Status: {res1.metadata.get('response_status')}")
    print(f"  Uploaded Notes : {len(edu1.get('uploaded_notes', []))}")
    print(f"  Trusted Web    : {len(edu1.get('trusted_web', []))}")
    print(f"  Wikipedia      : {len(edu1.get('wikipedia', []))}")
    assert len(edu1.get('uploaded_notes', [])) > 0, "TEST 1 Failed: Uploaded notes should be > 0"
    assert len(edu1.get('trusted_web', [])) == 0, "TEST 1 Failed: External web should be 0"
    print("  ✅ TEST 1 PASSED!")

    # -------------------------------------------------------------------------
    # TEST 2: Strict Document Missing Evidence
    # -------------------------------------------------------------------------
    print("\n--- [TEST 2] Strict Document Missing Evidence ---")
    q2 = "According to my uploaded document, what is the battery capacity?"
    plan2 = RuleBasedPlannerEngine.generate_plan(q2, available_docs=["Vector_DB_Docs.pdf"])
    res2 = orch.run({"query": q2, "execution_plan": plan2, "doc_filter": ["Vector_DB_Docs.pdf"]})
    edu2 = agent_response_adapter.compose_from_agent_result(res2)

    print(f"  Strategy        : {plan2.source_strategy.value}")
    print(f"  Response Status : {res2.metadata.get('response_status')}")
    print(f"  Uploaded Notes  : {len(edu2.get('uploaded_notes', []))}")
    print(f"  Trusted Web     : {len(edu2.get('trusted_web', []))}")
    print(f"  Wikipedia       : {len(edu2.get('wikipedia', []))}")
    print(f"  Code Examples   : {len(edu2.get('code_examples', []))}")
    assert res2.metadata.get('response_status') == "INSUFFICIENT_EVIDENCE", "TEST 2 Failed: Status must be INSUFFICIENT_EVIDENCE"
    assert len(edu2.get('trusted_web', [])) == 0, "TEST 2 Failed: Web search must NOT occur!"
    assert len(edu2.get('code_examples', [])) == 0, "TEST 2 Failed: Code examples must be 0!"
    print("  ✅ TEST 2 PASSED!")

    # -------------------------------------------------------------------------
    # TEST 3: Explicit GitHub Request
    # -------------------------------------------------------------------------
    print("\n--- [TEST 3] Explicit GitHub Request ---")
    q3 = "I want to learn Docker from beginner to advanced. Recommend useful GitHub repositories."
    plan3 = RuleBasedPlannerEngine.generate_plan(q3, available_docs=[])
    res3 = orch.run({"query": q3, "execution_plan": plan3})
    edu3 = agent_response_adapter.compose_from_agent_result(res3)

    code_repos = edu3.get('code_examples', [])
    print(f"  Strategy      : {plan3.source_strategy.value}")
    print(f"  Code Examples : {len(code_repos)}")
    if code_repos:
        for idx, item in enumerate(code_repos[:3], 1):
            print(f"    [{idx}] Title: {item.get('title')} | URL: {item.get('url')} | Provider: {item.get('provider')}")
    assert len(code_repos) > 0, "TEST 3 Failed: code_examples must be populated!"
    assert all("github.com" in repo.get('url', '') for repo in code_repos), "TEST 3 Failed: All code_examples must have github.com URLs!"
    print("  ✅ TEST 3 PASSED!")

    # -------------------------------------------------------------------------
    # TEST 4: Mixed Resource Request
    # -------------------------------------------------------------------------
    print("\n--- [TEST 4] Mixed Resource Request ---")
    q4 = "Explain Docker architecture briefly and recommend YouTube videos and GitHub repositories to learn it."
    plan4 = RuleBasedPlannerEngine.generate_plan(q4, available_docs=[])
    res4 = orch.run({"query": q4, "execution_plan": plan4})
    edu4 = agent_response_adapter.compose_from_agent_result(res4)

    print(f"  Videos        : {len(edu4.get('videos', []))}")
    print(f"  Code Examples : {len(edu4.get('code_examples', []))}")
    assert len(edu4.get('videos', [])) > 0, "TEST 4 Failed: videos must be > 0"
    assert len(edu4.get('code_examples', [])) > 0, "TEST 4 Failed: code_examples must be > 0"
    print("  ✅ TEST 4 PASSED!")

    # -------------------------------------------------------------------------
    # TEST 5: General Query
    # -------------------------------------------------------------------------
    print("\n--- [TEST 5] General Query ---")
    q5 = "Explain how transformers work."
    plan5 = RuleBasedPlannerEngine.generate_plan(q5, available_docs=[])
    res5 = orch.run({"query": q5, "execution_plan": plan5})
    edu5 = agent_response_adapter.compose_from_agent_result(res5)

    print(f"  Strategy      : {plan5.source_strategy.value}")
    print(f"  Response Status: {res5.metadata.get('response_status')}")
    assert res5.metadata.get('response_status') == "SUCCESS", "TEST 5 Failed: Status must be SUCCESS"
    print("  ✅ TEST 5 PASSED!")

    print("\n" + "=" * 80)
    print("ALL PHASE 8B AUTOMATED VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    test_phase8b_scenarios()
