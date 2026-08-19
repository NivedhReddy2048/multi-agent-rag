import sys
import os
sys.path.insert(0, os.path.abspath("."))
import json
import traceback
from langchain_core.documents import Document
from config.settings import Config
from agents.orchestrator import OrchestratorAgent
from agents.synthesis import SynthesisAgent
from core.llm_manager import LLMManager
from core.llm.base_provider import LLMResponse
from core.planner.rules import RuleBasedPlannerEngine
from core.synthesis.agent_response_adapter import agent_response_adapter
from core.memory import ConversationMemory

def log_debug(msg):
    sys.stderr.write(f"[DEBUG] {msg}\n")
    sys.stderr.flush()

def mock_llm_generate(self, prompt_or_chain_fn, inputs=None, **kwargs):
    log_debug(f"inside mock_llm_generate (kwargs keys: {list(kwargs.keys())})")
    query = kwargs.get("query") or "RAG Architecture"
    mock_content = (
        f"### Educational Analysis for: '{query}'\n\n"
        f"Retrieval-Augmented Generation (RAG) combines dense vector retrieval with LLM generation to reduce hallucinations [1].\n\n"
        f"#### Core Concepts & Architecture\n"
        f"Key mechanisms include semantic indexing, cross-encoder reranking, and evidence-grounded synthesis [1].\n"
        f"Peer-reviewed research emphasizes factual validation and claim-level grounding [2]."
    )
    return LLMResponse(
        provider="mock_groq",
        model="gpt-oss-20b",
        content=mock_content,
        latency=12.5,
        tokens=250,
        success=True,
        error="",
        fallback_occurred=False,
        fallback_chain=["mock_groq"],
        prompt_tokens=100,
        completion_tokens=150,
        attempts_detail=[],
        prompt_builder_used=True,
        prompt_length_chars=len(mock_content)
    )

LLMManager.generate = mock_llm_generate

# Completely safe mock for SynthesisAgent.run to evaluate orchestrator & validation downstream telemetry cleanly
def _bulletproof_synth_run(self, context):
    log_debug("inside _bulletproof_synth_run")
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
    
    from agents.base import AgentResult
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
    """Lightweight engine mock for document retrieval in audit testing."""
    def __init__(self, cfg):
        self.cfg = cfg

    def dense_search(self, query, k=8, doc_filter=None):
        if not doc_filter:
            return []
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


def run_runtime_audit():
    log_debug("Entering run_runtime_audit()")

    cfg = Config()
    engine = MockRAGEngine(cfg)
    memory = ConversationMemory(":memory:")
    orch = OrchestratorAgent(cfg, engine, memory)
    log_debug("Initialized OrchestratorAgent")

    test_queries = [
        ("TEST A", "Explain Retrieval-Augmented Generation in detail.", None),
        ("TEST B", "What are the important research papers on RAG hallucination and why are they important?", None),
        ("TEST C", "I want to learn Docker from beginner to advanced. Give me a learning explanation and recommend useful YouTube videos and GitHub repositories.", None),
        ("TEST D", "Explain RAG hallucination and give me research papers, videos, and useful GitHub repositories.", None),
        ("TEST E", "Explain Transformers in detail using my uploaded document and external sources.", ["Transformer_Architecture.pdf"]),
        ("TEST F", "Answer strictly according to my uploaded document.", ["Transformer_Architecture.pdf"]),
    ]

    results = []

    for test_id, query, docs in test_queries:
        log_debug(f"Starting test iteration: {test_id}")

        try:
            # 1. Generate ExecutionPlan
            plan = RuleBasedPlannerEngine.generate_plan(query, available_docs=docs or [])
            log_debug(f"Plan generated: {plan.intent}")

            # 2. Run Orchestrator
            ctx = {"query": query, "execution_plan": plan, "available_documents": docs or []}
            log_debug("Calling orch.run()")
            agent_res = orch.run(ctx)
            log_debug("orch.run() returned successfully")

            # Read debug prompt snippet if created
            debug_prompt = ""
            if os.path.exists("debug/final_prompt.txt"):
                with open("debug/final_prompt.txt", "r", encoding="utf-8") as f:
                    debug_prompt = f.read()

            # 3. Adapter Conversion
            log_debug("Calling agent_response_adapter")
            edu_res = agent_response_adapter.compose_from_agent_result(agent_res)

            # 4. Extract telemetry
            sources = agent_res.sources or []
            prov_counts = {}
            for s in sources:
                p = s.get("provider", "unknown")
                prov_counts[p] = prov_counts.get(p, 0) + 1

            res_summary = {
                "test_id": test_id,
                "query": query,
                "intent": plan.intent.value,
                "source_strategy": plan.source_strategy.value,
                "selected_sources": [s.value for s in plan.selected_sources],
                "doc_usage_mode": plan.document_usage_mode.value if hasattr(plan.document_usage_mode, 'value') else str(plan.document_usage_mode),
                "dispatched_provider_counts": prov_counts,
                "total_sources_retrieved": len(sources),
                "response_status": edu_res.get("response_status"),
                "agent_trace": agent_res.agent_trace,
                "content_preview": agent_res.content[:300] if agent_res.content else "",
                "debug_prompt_snippet": debug_prompt[:600] if debug_prompt else "",
                "categories_in_edu_res": {
                    "uploaded_notes": len(edu_res.get("uploaded_notes", [])),
                    "trusted_web": len(edu_res.get("trusted_web", [])),
                    "wikipedia": len(edu_res.get("wikipedia", [])),
                    "research": len(edu_res.get("research", [])),
                    "books": len(edu_res.get("books", [])),
                    "videos": len(edu_res.get("videos", [])),
                    "code_examples": len(edu_res.get("code_examples", [])),
                }
            }

            log_debug(f"Summary computed for {test_id}: {res_summary['categories_in_edu_res']}")
            results.append(res_summary)
        except Exception as e:
            log_debug(f"EXCEPTION IN {test_id}: {type(e).__name__}: {e}")
            traceback.print_exc(file=sys.stderr)

    log_debug("Writing json output")
    with open("scratch/phase8_runtime_audit_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    log_debug("FINISHED AUDIT SUITE")


if __name__ == "__main__":
    try:
        run_runtime_audit()
    except Exception as e:
        log_debug(f"TOP-LEVEL ERROR: {e}")
        traceback.print_exc(file=sys.stderr)
