"""Targeted Phase 7C Test Suite verifying Intent, Document Usage Policy, Source Selection Matrix, and Orchestration."""

import sys
from typing import List
from core.planner.rules import RuleBasedPlannerEngine
from core.planner.enums import EducationalIntent, SourceStrategy, DocumentUsageMode
from core.models.domain import SourceType


def run_tests():
    print("=" * 70)
    print("RUNNING EKIP PHASE 7C HARDENING TEST SUITE")
    print("=" * 70)

    # Simulated available uploaded docs
    available_docs = ["python_basics.pdf", "transformer_notes.pdf", "rag_notes.txt"]

    # ----------------------------------------------------
    # TEST 1: Unrelated document ("Explain theory of relativity")
    # ----------------------------------------------------
    q1 = "Explain the theory of relativity."
    plan1 = RuleBasedPlannerEngine.generate_plan(q1, available_docs=available_docs)
    print(f"\n[Test 1] Query: '{q1}'")
    print(f"  Target Docs: {plan1.target_documents}")
    print(f"  Doc Usage Mode: {plan1.document_usage_mode.value}")
    print(f"  Source Strategy: {plan1.source_strategy.value}")
    print(f"  Selected Sources: {[s.value for s in plan1.selected_sources]}")
    assert plan1.document_usage_mode == DocumentUsageMode.EXCLUDED, f"Expected EXCLUDED, got {plan1.document_usage_mode}"
    assert SourceType.INTERNAL_DOCUMENT not in plan1.selected_sources, "Internal document should not be selected"
    print("  ✅ TEST 1 PASSED: Unrelated document excluded.")

    # ----------------------------------------------------
    # TEST 2: Explicit document request ("Explain attention according to my uploaded notes")
    # ----------------------------------------------------
    q2 = "Explain attention according to my uploaded notes."
    plan2 = RuleBasedPlannerEngine.generate_plan(q2, available_docs=available_docs)
    print(f"\n[Test 2] Query: '{q2}'")
    print(f"  Target Docs: {plan2.target_documents}")
    print(f"  Doc Usage Mode: {plan2.document_usage_mode.value}")
    print(f"  Source Strategy: {plan2.source_strategy.value}")
    print(f"  Selected Sources: {[s.value for s in plan2.selected_sources]}")
    assert plan2.document_usage_mode == DocumentUsageMode.REQUIRED, f"Expected REQUIRED, got {plan2.document_usage_mode}"
    assert SourceType.INTERNAL_DOCUMENT in plan2.selected_sources, "Internal document should be selected"
    print("  ✅ TEST 2 PASSED: Explicit document request REQUIRED.")

    # ----------------------------------------------------
    # TEST 3: Topic overlap ("Explain transformers in detail.")
    # ----------------------------------------------------
    q3 = "Explain transformers in detail."
    plan3 = RuleBasedPlannerEngine.generate_plan(q3, available_docs=available_docs)
    print(f"\n[Test 3] Query: '{q3}'")
    print(f"  Target Docs: {plan3.target_documents}")
    print(f"  Doc Usage Mode: {plan3.document_usage_mode.value}")
    print(f"  Source Strategy: {plan3.source_strategy.value}")
    print(f"  Selected Sources: {[s.value for s in plan3.selected_sources]}")
    assert plan3.document_usage_mode == DocumentUsageMode.PREFERRED, f"Expected PREFERRED, got {plan3.document_usage_mode}"
    assert SourceType.INTERNAL_DOCUMENT in plan3.selected_sources, "Internal document should be preferred"
    assert len(plan3.selected_sources) > 1, "Should include external sources alongside internal docs"
    print("  ✅ TEST 3 PASSED: Topic overlap PREFERRED with multi-source collection.")

    # ----------------------------------------------------
    # TEST 4: YouTube recommendation ("Recommend good YouTube videos for learning Docker.")
    # ----------------------------------------------------
    q4 = "Recommend good YouTube videos for learning Docker."
    plan4 = RuleBasedPlannerEngine.generate_plan(q4, available_docs=available_docs)
    print(f"\n[Test 4] Query: '{q4}'")
    print(f"  Intent: {plan4.intent.value}")
    print(f"  Doc Usage Mode: {plan4.document_usage_mode.value}")
    print(f"  Selected Sources: {[s.value for s in plan4.selected_sources]}")
    assert plan4.intent == EducationalIntent.VIDEO_RECOMMENDATION, f"Expected VIDEO_RECOMMENDATION, got {plan4.intent}"
    assert SourceType.VIDEO in plan4.selected_sources, "SourceType.VIDEO must be selected"
    assert plan4.document_usage_mode == DocumentUsageMode.EXCLUDED, "Internal docs excluded for YouTube query"
    print("  ✅ TEST 4 PASSED: YouTube video recommendation source activated.")

    # ----------------------------------------------------
    # TEST 5: Research papers ("Find research papers about hallucination in RAG systems.")
    # ----------------------------------------------------
    q5 = "Find research papers about hallucination in RAG systems."
    plan5 = RuleBasedPlannerEngine.generate_plan(q5, available_docs=available_docs)
    print(f"\n[Test 5] Query: '{q5}'")
    print(f"  Intent: {plan5.intent.value}")
    print(f"  Doc Usage Mode: {plan5.document_usage_mode.value}")
    print(f"  Selected Sources: {[s.value for s in plan5.selected_sources]}")
    assert plan5.intent == EducationalIntent.RESEARCH_DISCOVERY, f"Expected RESEARCH_DISCOVERY, got {plan5.intent}"
    assert SourceType.ARXIV in plan5.selected_sources, "SourceType.ARXIV must be selected"
    assert SourceType.SEMANTIC_SCHOLAR in plan5.selected_sources, "SourceType.SEMANTIC_SCHOLAR must be selected"
    print("  ✅ TEST 5 PASSED: Research papers sources activated (arXiv + Semantic Scholar).")

    # ----------------------------------------------------
    # TEST 6: GitHub resources ("Recommend GitHub repositories to learn FastAPI.")
    # ----------------------------------------------------
    q6 = "Recommend GitHub repositories to learn FastAPI."
    plan6 = RuleBasedPlannerEngine.generate_plan(q6, available_docs=available_docs)
    print(f"\n[Test 6] Query: '{q6}'")
    print(f"  Intent: {plan6.intent.value}")
    print(f"  Selected Sources: {[s.value for s in plan6.selected_sources]}")
    assert plan6.intent == EducationalIntent.CODE_RESOURCE_RECOMMENDATION, f"Expected CODE_RESOURCE_RECOMMENDATION, got {plan6.intent}"
    assert SourceType.GITHUB_REPO in plan6.selected_sources, "SourceType.GITHUB_REPO must be selected"
    print("  ✅ TEST 6 PASSED: GitHub repository source activated.")

    # ----------------------------------------------------
    # TEST 7: General explanation without documents ("Explain entropy in information theory in detail.")
    # ----------------------------------------------------
    q7 = "Explain entropy in information theory in detail."
    plan7 = RuleBasedPlannerEngine.generate_plan(q7, available_docs=available_docs)
    print(f"\n[Test 7] Query: '{q7}'")
    print(f"  Doc Usage Mode: {plan7.document_usage_mode.value}")
    print(f"  Source Strategy: {plan7.source_strategy.value}")
    print(f"  Selected Sources: {[s.value for s in plan7.selected_sources]}")
    assert plan7.document_usage_mode == DocumentUsageMode.EXCLUDED, "Internal docs should be EXCLUDED"
    assert plan7.source_strategy == SourceStrategy.GENERAL_KNOWLEDGE, "Strategy should be GENERAL_KNOWLEDGE"
    print("  ✅ TEST 7 PASSED: General explanation uses GENERAL_KNOWLEDGE without document dependency.")

    # ----------------------------------------------------
    # TEST 8: Follow-up query ("Explain transformers", then "Now recommend research papers about that.")
    # ----------------------------------------------------
    history = [
        {"role": "user", "content": "Explain transformers."},
        {"role": "assistant", "content": "Transformers are neural network architectures utilizing self-attention..."}
    ]
    q8 = "Now recommend research papers about that."
    plan8 = RuleBasedPlannerEngine.generate_plan(q8, history=history, available_docs=available_docs)
    print(f"\n[Test 8] Query: '{q8}'")
    print(f"  Intent: {plan8.intent.value}")
    print(f"  Selected Sources: {[s.value for s in plan8.selected_sources]}")
    assert plan8.intent == EducationalIntent.RESEARCH_DISCOVERY, f"Expected RESEARCH_DISCOVERY, got {plan8.intent}"
    assert SourceType.ARXIV in plan8.selected_sources, "SourceType.ARXIV must be selected for follow-up paper request"
    print("  ✅ TEST 8 PASSED: Follow-up intent successfully resolved.")

    print("\n" + "=" * 70)
    print("ALL 8 PHASE 7C UNIT TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
