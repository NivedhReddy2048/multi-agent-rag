import sys
import os
sys.path.insert(0, os.path.abspath("."))
import json
import traceback
from typing import Dict, Any, List
from langchain_core.documents import Document

from config.settings import Config
from core.planner.rules import RuleBasedPlannerEngine
from core.orchestrator.knowledge_orchestrator import KnowledgeOrchestrator
from agents.orchestrator import OrchestratorAgent
from agents.sources import GithubKnowledgeAgent
from core.providers import provider_registry
from core.synthesis.agent_response_adapter import agent_response_adapter
from core.memory import ConversationMemory
from core.llm_manager import LLMManager
from core.llm.base_provider import LLMResponse
from agents.synthesis import SynthesisAgent
from agents.base import AgentResult

def mock_llm_generate(self, prompt_or_chain_fn, inputs=None, **kwargs):
    query = kwargs.get("query") or "Topic Explanation"
    mock_content = (
        f"### Diagnostic Synthesis for: '{query}'\n\n"
        f"Retrieval-Augmented Generation provides structured evidence grounding [1].\n"
        f"Key resources include peer-reviewed papers, videos, and GitHub repositories [2]."
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
    
    mock_content = (
        f"### Educational Guide: {query}\n\n"
        f"Retrieval-Augmented Generation (RAG) integrates dense retrieval with neural generation [1].\n\n"
        f"#### Key Evidence & Insights\n"
        f"Verified research demonstrates that grounded synthesis significantly mitigates model hallucination [1].\n"
        f"Multi-source collection integrates peer-reviewed papers, open-source repositories, and encyclopedic knowledge [2]."
    )
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


class MockRAGEngine:
    """Mock engine simulating workspace with an indexed document."""
    def __init__(self, cfg):
        self.cfg = cfg

    def dense_search(self, query, k=8, doc_filter=None):
        return [
            Document(
                page_content="Transformers use self-attention mechanisms to process input sequences in parallel. Positional encodings provide sequence order information.",
                metadata={"source_file": "Transformer_Architecture.pdf", "page_number": 1, "chunk_id": "transformer_chunk_1"}
            )
        ]

    def sparse_search(self, query, k=8, doc_filter=None):
        return self.dense_search(query, k, doc_filter)

    def reciprocal_rank_fusion(self, dense, sparse):
        return dense

    def rerank(self, query, fused, top_k=6, min_score_override=None):
        for d in fused:
            d.metadata["score"] = 5.2
        return [(d, 5.2) for d in fused]

    def compress_context(self, reranked, max_chunks=6):
        return [d for d, _ in reranked]

    def confidence(self):
        return 85

    def list_docs(self):
        return {"Transformer_Architecture.pdf": {"chunks": 10, "pages": 5, "uploaded": "2026-08-18", "size_mb": 1.2}}


def run_phase8a_diagnostic():
    print("=" * 80)
    print("EKIP PHASE 8A — INSTRUMENTED RUNTIME TRUTH & SOURCE INTEGRITY AUDIT")
    print("=" * 80)

    cfg = Config()
    engine = MockRAGEngine(cfg)
    memory = ConversationMemory(":memory:")
    orch = OrchestratorAgent(cfg, engine, memory)

    # Directly test GithubProvider status
    github_provider = provider_registry.get_provider("github")
    print(f"\n🔍 [PROVIDER AUDIT] GitHub Provider Status:")
    print(f"  - Configured Token Present: {bool(github_provider.api_key)}")
    print(f"  - Initialized: {github_provider.is_initialized}")
    if github_provider:
        h_res = github_provider.health_check()
        print(f"  - Health Check Status: {h_res.status} | Success: {h_res.success} | Error: {h_res.error}")

    # =========================================================================
    # DIAGNOSTIC TEST C: EXPLICIT GITHUB REQUEST
    # =========================================================================
    print("\n" + "=" * 80)
    print("RUNNING DIAGNOSTIC: TEST C (Explicit GitHub Request)")
    print("Query: 'I want to learn Docker from beginner to advanced. Give me a learning explanation and recommend useful YouTube videos and GitHub repositories.'")
    print("=" * 80)

    query_c = "I want to learn Docker from beginner to advanced. Give me a learning explanation and recommend useful YouTube videos and GitHub repositories."
    plan_c = RuleBasedPlannerEngine.generate_plan(query_c, available_docs=[])

    print(f"1. ExecutionPlan Intent         : {plan_c.intent.value}")
    print(f"2. ExecutionPlan SelectedSources: {[s.value for s in plan_c.selected_sources]}")
    print(f"   - GITHUB_REPO in Plan?      : {'github_repo' in [s.value for s in plan_c.selected_sources]}")

    # Inspect GithubKnowledgeAgent standalone execution
    gh_agent = GithubKnowledgeAgent()
    gh_raw_results = gh_agent.execute(query_c, max_results=5)
    print(f"3. GithubKnowledgeAgent Direct Return Count: {len(gh_raw_results)}")
    if gh_raw_results:
        for idx, item in enumerate(gh_raw_results, 1):
            print(f"   [{idx}] Title: {item.title} | Provider: {item.provider} | SourceType: {item.source_type} | URL: {item.url}")
    else:
        print("   ⚠️ GithubKnowledgeAgent returned 0 items!")

    # Inspect KnowledgeOrchestrator collection for plan_c
    ko = KnowledgeOrchestrator()
    ko_coll_c = ko.collect(query_c, plan_c, timeout_seconds=10.0)
    print(f"4. KnowledgeOrchestrator Total Collected: {len(ko_coll_c.results)}")
    ko_c_by_type = {}
    for r in ko_coll_c.results:
        st = r.source_type.value if hasattr(r.source_type, 'value') else str(r.source_type)
        ko_c_by_type[st] = ko_c_by_type.get(st, 0) + 1
    print(f"   Collected Items Grouped by SourceType: {ko_c_by_type}")

    # Inspect dispatch & normalization inside OrchestratorAgent
    dispatched_c = orch.dispatch_selected_sources(query_c, plan_c, {"query": query_c})
    print(f"5. Dispatched Sources Count (Document + External): {len(dispatched_c['doc_sources']) + len(dispatched_c['external_sources'])}")
    ext_c_types = {}
    for s in dispatched_c['external_sources']:
        st = s.get("source_type")
        ext_c_types[st] = ext_c_types.get(st, 0) + 1
    print(f"   Normalized Dispatched External Sources: {ext_c_types}")

    # Full orchestrator run for TEST C
    res_c = orch.run({"query": query_c, "execution_plan": plan_c})
    edu_c = agent_response_adapter.compose_from_agent_result(res_c)
    print(f"6. AgentResult.sources Total Count: {len(res_c.sources or [])}")
    res_c_types = {}
    for s in (res_c.sources or []):
        st = s.get("source_type", s.get("provider", "unknown"))
        res_c_types[st] = res_c_types.get(st, 0) + 1
    print(f"   AgentResult.sources Grouped by SourceType: {res_c_types}")
    print(f"7. EducationalResponse UI Categories:")
    print(f"   - uploaded_notes : {len(edu_c.get('uploaded_notes', []))}")
    print(f"   - trusted_web    : {len(edu_c.get('trusted_web', []))}")
    print(f"   - wikipedia      : {len(edu_c.get('wikipedia', []))}")
    print(f"   - research       : {len(edu_c.get('research', []))}")
    print(f"   - books          : {len(edu_c.get('books', []))}")
    print(f"   - videos         : {len(edu_c.get('videos', []))}")
    print(f"   - code_examples  : {len(edu_c.get('code_examples', []))}")

    # =========================================================================
    # DIAGNOSTIC TEST E: DOCUMENT AUGMENTED MODE
    # =========================================================================
    print("\n" + "=" * 80)
    print("RUNNING DIAGNOSTIC: TEST E (Document Augmented Mode)")
    print("Query: 'Explain Transformers in detail using my uploaded document and external sources.'")
    print("=" * 80)

    query_e = "Explain Transformers in detail using my uploaded document and external sources."
    plan_e = RuleBasedPlannerEngine.generate_plan(query_e, available_docs=["Transformer_Architecture.pdf"])

    print(f"1. ExecutionPlan Intent         : {plan_e.intent.value}")
    print(f"2. ExecutionPlan TargetDocs     : {plan_e.target_documents}")
    print(f"3. ExecutionPlan SelectedSources: {[s.value for s in plan_e.selected_sources]}")
    print(f"4. DocumentUsageMode            : {plan_e.document_usage_mode.value if hasattr(plan_e.document_usage_mode, 'value') else plan_e.document_usage_mode}")

    # Run dispatch explicitly
    ctx_e = {"query": query_e, "execution_plan": plan_e, "target_documents": plan_e.target_documents, "doc_filter": plan_e.target_documents}
    dispatched_e = orch.dispatch_selected_sources(query_e, plan_e, ctx_e, doc_filter=plan_e.target_documents)

    doc_sources_e = dispatched_e["doc_sources"]
    ext_sources_e = dispatched_e["external_sources"]
    print(f"5. Chunks Retrieved from Uploaded Document : {len(doc_sources_e)}")
    if doc_sources_e:
        print(f"   Sample Chunk Metadata: {doc_sources_e[0].get('metadata')}")

    # CRAG Evaluation for TEST E
    crag_res_e = orch.crag.run({
        "query": query_e,
        "documents": doc_sources_e,
        "source_strategy": plan_e.source_strategy,
        "execution_plan": plan_e
    })
    print(f"6. CRAG Evaluation Result                   : Sufficient={crag_res_e.metadata.get('sufficient')} | Score={crag_res_e.metadata.get('retrieval_score')}")

    # Full orchestrator run for TEST E
    res_e = orch.run(ctx_e)
    edu_e = agent_response_adapter.compose_from_agent_result(res_e)

    doc_in_final = [s for s in (res_e.sources or []) if s.get('source_type') == 'internal_document']
    print(f"7. Chunks Included in final_sources         : {len(doc_in_final)}")
    print(f"8. Chunks Present in AgentResult.sources    : {len(doc_in_final)}")
    print(f"9. Number Categorized as uploaded_notes      : {len(edu_e.get('uploaded_notes', []))}")
    if edu_e.get('uploaded_notes'):
        print(f"   uploaded_notes Content Sample: {edu_e.get('uploaded_notes')[0]}")
    else:
        print("   ⚠️ uploaded_notes is EMPTY in EducationalResponse!")

    # =========================================================================
    # DIAGNOSTIC TEST F: STRICT DOCUMENT MODE
    # =========================================================================
    print("\n" + "=" * 80)
    print("RUNNING DIAGNOSTIC: TEST F (Strict Document Mode)")
    print("Query: 'Answer strictly according to my uploaded document.'")
    print("=" * 80)

    query_f = "Answer strictly according to my uploaded document."
    plan_f = RuleBasedPlannerEngine.generate_plan(query_f, available_docs=["Transformer_Architecture.pdf"])

    print(f"1. ExecutionPlan Intent         : {plan_f.intent.value}")
    print(f"2. ExecutionPlan Strategy       : {plan_f.source_strategy.value}")
    print(f"3. ExecutionPlan TargetDocs     : {plan_f.target_documents}")
    print(f"4. ExecutionPlan SelectedSources: {[s.value for s in plan_f.selected_sources]}")
    print(f"5. DocumentUsageMode            : {plan_f.document_usage_mode.value if hasattr(plan_f.document_usage_mode, 'value') else plan_f.document_usage_mode}")

    # Case F1: When target_documents IS passed (matching document found)
    ctx_f1 = {"query": query_f, "execution_plan": plan_f, "target_documents": plan_f.target_documents, "doc_filter": plan_f.target_documents}
    dispatched_f1 = orch.dispatch_selected_sources(query_f, plan_f, ctx_f1, doc_filter=plan_f.target_documents)
    print(f"\n--- Case F1: Document Matched & Retrieved ({len(dispatched_f1['doc_sources'])} chunks) ---")
    res_f1 = orch.run(ctx_f1)
    edu_f1 = agent_response_adapter.compose_from_agent_result(res_f1)
    print(f"   AgentResult.sources count : {len(res_f1.sources or [])}")
    print(f"   EducationalResponse UI distribution:")
    print(f"     - uploaded_notes: {len(edu_f1.get('uploaded_notes', []))}")
    print(f"     - trusted_web   : {len(edu_f1.get('trusted_web', []))}")
    print(f"     - wikipedia     : {len(edu_f1.get('wikipedia', []))}")

    # Case F2: When target_documents IS NOT passed or 0 chunks retrieved
    ctx_f2 = {"query": query_f, "execution_plan": plan_f}
    print(f"\n--- Case F2: Document NOT Matched / 0 Chunks Retrieved ---")
    dispatched_f2 = orch.dispatch_selected_sources(query_f, plan_f, ctx_f2, doc_filter=None)
    print(f"   Dispatched Doc Chunks: {len(dispatched_f2['doc_sources'])} | External: {len(dispatched_f2['external_sources'])}")
    res_f2 = orch.run(ctx_f2)
    edu_f2 = agent_response_adapter.compose_from_agent_result(res_f2)
    print(f"   AgentResult.sources count : {len(res_f2.sources or [])}")
    if res_f2.sources:
        for idx, src in enumerate(res_f2.sources, 1):
            print(f"     Source [{idx}]: Title='{src.get('title')}' | Provider='{src.get('provider')}' | SourceType='{src.get('source_type')}' | SourceFile='{src.get('source_file')}' | URL='{src.get('url')}'")
    print(f"   EducationalResponse UI distribution:")
    print(f"     - uploaded_notes: {len(edu_f2.get('uploaded_notes', []))}")
    print(f"     - trusted_web   : {len(edu_f2.get('trusted_web', []))}")
    print(f"     - wikipedia     : {len(edu_f2.get('wikipedia', []))}")

    print("\n" + "=" * 80)
    print("DIAGNOSTIC AUDIT COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    run_phase8a_diagnostic()
