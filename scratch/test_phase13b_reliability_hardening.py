"""EKIP Phase 13B Universal Query Reliability Hardening Verification Suite (Pytest Edition).

Tests:
1. Group 1: Intent Routing & Preprocessing Normalization (Dockerfile, preprints, libraries, skills, vids, diff between, etc.)
2. Group 2: Follow-Up Context Resolution (Mode A history vs Mode B no-history clarification)
3. Group 3: Deterministic Synthetic Fallback (Quiz generation under LLM outages)
4. Group 4: Compound Multi-Intent Resolution & Execution Plan
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from core.planner.rules import RuleBasedPlannerEngine
from core.planner.enums import EducationalIntent
from core.models.domain import SourceType
from agents.orchestrator import OrchestratorAgent


@pytest.mark.parametrize("query,expected_intent", [
    ("Write a Dockerfile for a FastAPI application.", EducationalIntent.PROGRAMMING_HELP),
    ("How to connect PostgreSQL database in Node.js using pg library?", EducationalIntent.PROGRAMMING_HELP),
    ("can u code up a fast api server for me asap plzzzz", EducationalIntent.PROGRAMMING_HELP),
    ("Find recent preprints on Graph Neural Networks.", EducationalIntent.RESEARCH_DISCOVERY),
    ("Find Python libraries for time-series forecasting.", EducationalIntent.CODE_RESOURCE_RECOMMENDATION),
    ("What skills are needed for Data Platform Engineering?", EducationalIntent.CAREER_GUIDANCE),
    ("need 2 know diff between process and thread fast pls", EducationalIntent.COMPARISON),
    ("gimme sum good vids on pythn loops bro", EducationalIntent.VIDEO_RECOMMENDATION),
])
def test_group1_intent_routing_and_normalization(query, expected_intent):
    plan = RuleBasedPlannerEngine.generate_plan(query)
    assert plan.intent == expected_intent, f"Query '{query}' expected intent '{expected_intent.value}', got '{plan.intent.value}'"


def test_group2_mode_b_followup_no_history():
    query_b = "Explain that second point in more detail."
    # Planner should classify as FOLLOW_UP
    plan = RuleBasedPlannerEngine.generate_plan(query_b, history=[])
    assert plan.intent == EducationalIntent.FOLLOW_UP

    # Fallback formatting test for Mode B clarification in orchestrator
    mock_orchestrator_res = OrchestratorAgent._format_evidence_fallback(query_b, EducationalIntent.FOLLOW_UP, [])
    assert mock_orchestrator_res == ""


def test_group2_mode_a_followup_with_history():
    query = "Explain that second point in more detail."
    history = [
        {"role": "user", "content": "Explain Transformer attention mechanisms."},
        {"role": "assistant", "content": "1. Multi-Head Attention allows joint context. 2. Positional Encodings inject order."}
    ]
    plan = RuleBasedPlannerEngine.generate_plan(query, history=history)
    assert plan.intent == EducationalIntent.FOLLOW_UP


def test_group3_synthetic_quiz_fallback():
    query_quiz = "Generate a 5-question quiz on Python OOP."
    plan = RuleBasedPlannerEngine.generate_plan(query_quiz)
    assert plan.intent == EducationalIntent.QUIZ_GENERATION

    # Test deterministic fallback formatting for quiz intent when sources are empty
    formatted = OrchestratorAgent._format_evidence_fallback(query_quiz, plan.intent, [], exec_plan=plan)
    assert "Practice Quiz" in formatted
    assert "Question 1" in formatted
    assert "Question 5" in formatted
    assert "Answer Key" in formatted


def test_group4_compound_multi_intent():
    query_compound = "Explain transformers and show me a GitHub implementation."
    plan = RuleBasedPlannerEngine.generate_plan(query_compound)
    assert plan.intent == EducationalIntent.CONCEPT_EXPLANATION
    assert EducationalIntent.CODE_RESOURCE_RECOMMENDATION in plan.secondary_intents
    assert SourceType.GITHUB_REPO in plan.selected_sources
