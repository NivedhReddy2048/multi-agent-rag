"""
EKIP Phase 9C — Read-Only Diagnostic Audit Script
Audits ranking formula, authority handling, conflict detection, and citation integrity.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

# Add workspace root to path
sys.path.insert(0, os.path.abspath("."))

from config.settings import Config
from agents.orchestrator import OrchestratorAgent
from core.planner.enums import SourceRole, SourceStrategy, EducationalIntent
from core.planner.execution_plan import ExecutionPlan


def run_phase9c_diagnostic():
    print("=" * 60, flush=True)
    print("EKIP PHASE 9C — READ-ONLY DIAGNOSTIC AUDIT RUNNER", flush=True)
    print("=" * 60, flush=True)

    # 1. Audit Ranking Formula with Controlled Inputs
    print("\n--- TEST E & AUDIT 3: RANKING & AUTHORITY TEST ---", flush=True)
    sources = [
        {
            "title": "Supervised Learning Overview Blog",
            "content": "Supervised learning uses labeled dataset for training.",
            "source_type": "trusted_web",
            "provider": "tavily",
            "url": "https://random-tech-blog.com/supervised-learning-difference",
            "score": 0.80,
        },
        {
            "title": "Machine Learning Foundations",
            "content": "Supervised learning relies on ground-truth targets, while unsupervised learning discovers latent structures.",
            "source_type": "arxiv",
            "provider": "arxiv",
            "url": "https://arxiv.org/abs/2301.00000",
            "authors": ["Author A"],
            "published_date": "2023-01-01",
            "score": 0.90,
        },
        {
            "title": "Wikipedia: Supervised Learning",
            "content": "Supervised learning is the machine learning task of learning a function that maps an input to an output.",
            "source_type": "wikipedia",
            "provider": "wikipedia",
            "url": "https://en.wikipedia.org/wiki/Supervised_learning",
            "score": 0.85,
        }
    ]

    query = "What is the difference between supervised and unsupervised learning?"
    ranked = OrchestratorAgent._rank_and_filter_evidence(sources, query, intent=EducationalIntent.CONCEPT_EXPLANATION)
    print("Ranked evidence order:", flush=True)
    for idx, s in enumerate(ranked, 1):
        print(f"  [{idx}] Role: {s.get('source_role')} | Title: {s.get('title')} | Score: {s.get('score')} | Type: {s.get('source_type')}", flush=True)

    # 2. Audit Conflict Detection
    print("\n--- TEST C & D: CONFLICT DETECTION AUDIT ---", flush=True)
    from agents.synthesis import SynthesisAgent
    cfg = Config()
    synth = SynthesisAgent(cfg)
    plan_doc = ExecutionPlan(
        query="How many attention heads does EKIP-Transformer use?",
        intent=EducationalIntent.CONCEPT_EXPLANATION,
        source_strategy=SourceStrategy.DOCUMENT_ONLY
    )
    conf_ctx = {
        "query": "How many attention heads does EKIP-Transformer use?",
        "execution_plan": plan_doc,
        "documents": [
            {
                "title": "Doc A",
                "content": "The EKIP-Transformer architecture uses 8 attention heads.",
                "source_type": "internal_document",
                "provider": "uploaded_documents",
                "source_role": "factual_evidence",
                "score": 0.9,
            },
            {
                "title": "Doc B",
                "content": "The EKIP-Transformer architecture uses 16 attention heads.",
                "source_type": "internal_document",
                "provider": "uploaded_documents",
                "source_role": "factual_evidence",
                "score": 0.88,
            }
        ],
        "source_strategy": "document_only"
    }

    prompt, inputs, intent, docs, q, mode, t_name, sys_msg, telem = synth._prepare_prompt_and_context(conf_ctx)
    print("Conflict detection in synthesis prompt:", flush=True)
    if "⚠️ DETECTED CONFLICTS IN EVIDENCE:" in sys_msg:
        print("  ✅ Numeric conflict detected!", flush=True)
        for line in sys_msg.split("\n"):
            if "⚠️" in line or "Discrepancy" in line or "Rule:" in line:
                print(f"    {line}", flush=True)
    else:
        print("  ❌ Conflict NOT detected!", flush=True)

    # 3. Audit Non-Numeric Conflict Detection
    plan_text = ExecutionPlan(
        query="Who is the lead author of the EKIP framework?",
        intent=EducationalIntent.CONCEPT_EXPLANATION,
        source_strategy=SourceStrategy.DOCUMENT_ONLY
    )
    conf_text_ctx = {
        "query": "Who is the lead author of the EKIP framework?",
        "execution_plan": plan_text,
        "documents": [
            {
                "title": "Doc A",
                "content": "The EKIP framework was created primarily by Dr. Alice Smith in 2024.",
                "source_type": "internal_document",
                "provider": "uploaded_documents",
                "source_role": "factual_evidence",
                "score": 0.9,
            },
            {
                "title": "Doc B",
                "content": "The EKIP framework was created primarily by Dr. Bob Jones in 2025.",
                "source_type": "internal_document",
                "provider": "uploaded_documents",
                "source_role": "factual_evidence",
                "score": 0.88,
            }
        ],
        "source_strategy": "document_only"
    }
    prompt2, inputs2, intent2, docs2, q2, mode2, t_name2, sys_msg2, telem2 = synth._prepare_prompt_and_context(conf_text_ctx)
    print("\nNon-Numeric Conflict Detection in synthesis prompt:", flush=True)
    if "⚠️ DETECTED CONFLICTS IN EVIDENCE:" in sys_msg2:
        print("  ✅ Textual conflict detected!", flush=True)
    else:
        print("  ❌ Textual conflict NOT detected! (Regex numeric checker missed non-numeric discrepancy)", flush=True)

    # 4. Audit Citation Alignment
    print("\n--- TEST A & CITATION TRACE AUDIT ---", flush=True)
    from core.synthesis.agent_response_adapter import agent_response_adapter
    from unittest.mock import patch
    from core.models.synthesis import LearningPath
    
    mock_res = MagicMock()
    mock_res.content = "Supervised learning uses labeled targets [1]. Unsupervised learning discovers latent structures [2]."
    mock_res.confidence = 88
    mock_res.sources = sources[:2]
    mock_res.success = True
    mock_res.error = ""
    mock_res.metadata = {"response_status": "SUCCESS", "faithfulness": 1.0}

    plan = ExecutionPlan(
        query=query,
        intent=EducationalIntent.CONCEPT_EXPLANATION,
        source_strategy=SourceStrategy.HYBRID
    )

    mock_lp = LearningPath(
        current_topic="Machine Learning",
        prerequisites=["Python"],
        next_topics=["Deep Learning"],
        advanced_topics=["Transformers"],
    )
    with patch("core.synthesis.guided_learning.guided_learning_engine.generate_guided_questions", return_value=["Q1", "Q2"]), \
         patch("core.synthesis.guided_learning.guided_learning_engine.generate_learning_path", return_value=mock_lp):
        adapted = agent_response_adapter.compose_from_agent_result(mock_res, plan=plan)

    print("Adapted citations output:", flush=True)
    for c in adapted.get("citations", []):
        print(f"  Citation [{c['id']}] -> Title: {c['title']} | Provider: {c['provider']} | Type: {c['source_type']}", flush=True)

    print("\n" + "=" * 60, flush=True)
    print("DIAGNOSTIC AUDIT COMPLETE", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    try:
        run_phase9c_diagnostic()
    except Exception as e:
        import traceback, sys
        print(f"Exception in diagnostic: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc(file=sys.stdout)
