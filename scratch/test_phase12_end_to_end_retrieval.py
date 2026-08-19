"""
EKIP Phase 12 — End-to-End Retrieval & Response Closure Audit Suite
Tests all 11 mandatory queries across intent classification, plan generation, source strategy, dispatch, retrieval, normalization, synthesis, and final UI rendering contract.
"""

import sys
import os
import time
import json
import traceback
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath("."))

from config.settings import Config
from core.auth.database import init_db
from core.chat.database import init_chat_db
from core.engine import BaseRAGEngine
from core.memory import ConversationMemory
from graph.builder import create_ekip_planning_graph
from agents.orchestrator import OrchestratorAgent


TEST_QUERIES = [
    {
        "id": 1,
        "category": "RESEARCH",
        "query": "Find key research paper abstracts on Retrieval-Augmented Generation.",
        "expected_intent": "RESEARCH_DISCOVERY",
        "expected_sources": ["arxiv", "semantic_scholar"],
    },
    {
        "id": 2,
        "category": "RESEARCH",
        "query": "Find key research paper abstracts on computer vision.",
        "expected_intent": "RESEARCH_DISCOVERY",
        "expected_sources": ["arxiv", "semantic_scholar"],
    },
    {
        "id": 3,
        "category": "RESEARCH",
        "query": "Find key research paper abstracts on YOLO",
        "expected_intent": "RESEARCH_DISCOVERY",
        "expected_sources": ["arxiv", "semantic_scholar"],
    },
    {
        "id": 4,
        "category": "RESEARCH",
        "query": "Find key research paper abstracts on AI in Health Care",
        "expected_intent": "RESEARCH_DISCOVERY",
        "expected_sources": ["arxiv", "semantic_scholar"],
    },
    {
        "id": 5,
        "category": "VIDEO",
        "query": "Recommend top learning video concepts for understanding neural networks.",
        "expected_intent": "VIDEO_RECOMMENDATION",
        "expected_sources": ["youtube"],
    },
    {
        "id": 6,
        "category": "VIDEO",
        "query": "Recommend top learning video concepts for understanding Database management systems",
        "expected_intent": "VIDEO_RECOMMENDATION",
        "expected_sources": ["youtube"],
    },
    {
        "id": 7,
        "category": "VIDEO",
        "query": "Recommend top learning video concepts for understanding Python",
        "expected_intent": "VIDEO_RECOMMENDATION",
        "expected_sources": ["youtube"],
    },
    {
        "id": 8,
        "category": "CONCEPT",
        "query": "What is encapsulation in Python?",
        "expected_intent": "CONCEPT_EXPLANATION",
        "expected_sources": ["general_ai", "wikipedia"],
    },
    {
        "id": 9,
        "category": "PROGRAMMING",
        "query": "Implement a REST API endpoint using Django.",
        "expected_intent": "PROGRAMMING_HELP",
        "expected_sources": ["general_ai"],
    },
    {
        "id": 10,
        "category": "CODE_RESOURCE",
        "query": "Find open-source implementations of RAG in Python.",
        "expected_intent": "CODE_RESOURCE_RECOMMENDATION",
        "expected_sources": ["github"],
    },
    {
        "id": 11,
        "category": "DOCUMENT",
        "query": "Summarize my uploaded document.",
        "expected_intent": "DOCUMENT_QUERY",
        "expected_sources": ["internal_document"],
    },
]


def run_phase12_audit():
    init_db()
    init_chat_db()

    engine = BaseRAGEngine(Config)
    memory = ConversationMemory(Config.OBSERVABILITY_DB)
    orch = OrchestratorAgent(Config, engine, memory)
    planning_graph = create_ekip_planning_graph()

    results_report = []

    print("=" * 100)
    print(" 🚀 EKIP PHASE 12 — END-TO-END RETRIEVAL CLOSURE AUDIT")
    print("=" * 100)

    for item in TEST_QUERIES:
        q_id = item["id"]
        q_text = item["query"]
        expected_intent = item["expected_intent"]
        cat = item["category"]

        print(f"\n[{q_id}/11] Testing Query ({cat}): '{q_text}'")
        t0 = time.time()

        # Step 1: Run Planning Graph
        plan_state = planning_graph.invoke({
            "question": q_text,
            "conversation_history": [],
            "execution_mode": "chat_planning",
            "skip_synthesis": True,
        })

        exec_plan = plan_state.get("execution_plan") if isinstance(plan_state, dict) else getattr(plan_state, "execution_plan", None)
        detected_intent = str(exec_plan.intent.value if hasattr(exec_plan.intent, "value") else exec_plan.intent)
        planner_strategy = str(exec_plan.source_strategy.value if hasattr(exec_plan.source_strategy, "value") else exec_plan.source_strategy)
        doc_usage_mode = str(exec_plan.document_usage_mode.value if hasattr(exec_plan.document_usage_mode, "value") else exec_plan.document_usage_mode)
        selected_sources = [s.value if hasattr(s, "value") else str(s) for s in (exec_plan.selected_sources or [])]

        # Step 2: Context setup
        ctx = {
            "query": q_text,
            "history": [],
            "filters": {},
            "execution_plan": exec_plan,
            "plan_state": plan_state,
        }

        # Step 3: Run Orchestrator
        try:
            res = orch.run(ctx)
            latency = (time.time() - t0) * 1000

            meta = res.metadata if isinstance(res.metadata, dict) else {}
            provider = meta.get("provider", "NONE")
            model = meta.get("model", "none")
            source_mode = meta.get("source_mode", "none")
            confidence = res.confidence
            sources_retrieved = res.sources or []
            content_len = len(res.content) if res.content else 0

            # Count specialized item types retrieved
            papers_count = sum(1 for s in sources_retrieved if str(s.get("source_type", s.get("provider", ""))).lower() in ("arxiv", "semantic_scholar", "research"))
            videos_count = sum(1 for s in sources_retrieved if str(s.get("source_type", s.get("provider", ""))).lower() in ("youtube", "video"))
            repos_count = sum(1 for s in sources_retrieved if str(s.get("source_type", s.get("provider", ""))).lower() in ("github_repo", "github"))
            urls_in_content = res.content.count("http://") + res.content.count("https://") if res.content else 0
            abstracts_in_content = res.content.lower().count("abstract") if res.content else 0

            audit_entry = {
                "id": q_id,
                "query": q_text,
                "category": cat,
                "detected_intent": detected_intent,
                "expected_intent": expected_intent,
                "planner_strategy": planner_strategy,
                "doc_usage_mode": doc_usage_mode,
                "selected_sources": selected_sources,
                "sources_retrieved_count": len(sources_retrieved),
                "papers_count": papers_count,
                "videos_count": videos_count,
                "repos_count": repos_count,
                "urls_in_content": urls_in_content,
                "abstracts_in_content": abstracts_in_content,
                "content_len": content_len,
                "confidence": confidence,
                "provider": provider,
                "model": model,
                "source_mode": source_mode,
                "latency_ms": int(latency),
                "success": res.success and content_len > 0 and provider != "NONE",
                "error": res.error,
                "snippet": res.content[:200].replace("\n", " ") if res.content else "",
            }

            print(f"  Intent          : {detected_intent} (Expected: {expected_intent})")
            print(f"  Planner Strategy: {planner_strategy}")
            print(f"  Selected Sources: {selected_sources}")
            print(f"  Retrieved Count : {len(sources_retrieved)} items (Papers: {papers_count}, Videos: {videos_count}, Repos: {repos_count})")
            print(f"  Response Length : {content_len} chars | Confidence: {confidence}% | Provider: {provider}/{model}")
            print(f"  Content Snippet : {audit_entry['snippet']}")
            print(f"  Status          : {'PASS ✅' if audit_entry['success'] else 'FAIL ❌'}")

            results_report.append(audit_entry)

        except Exception as e:
            traceback.print_exc()
            results_report.append({
                "id": q_id,
                "query": q_text,
                "category": cat,
                "detected_intent": detected_intent,
                "expected_intent": expected_intent,
                "success": False,
                "error": str(e),
            })

    # Save summary report
    with open("scratch/phase12_audit_report.json", "w", encoding="utf-8") as f:
        json.dump(results_report, f, indent=2)

    print("\n" + "=" * 100)
    print(" 📊 PHASE 12 DIAGNOSTIC AUDIT SUMMARY")
    print("=" * 100)
    passed = sum(1 for r in results_report if r.get("success"))
    print(f" TOTAL PASSED: {passed}/{len(TEST_QUERIES)}")
    print(" Saved detailed JSON to scratch/phase12_audit_report.json")
    print("=" * 100)


if __name__ == "__main__":
    run_phase12_audit()
