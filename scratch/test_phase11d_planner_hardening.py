"""
EKIP Phase 11D — Minimal Planner Hardening Regression Test Suite.

Verifies fixes for:
1. Substring collision in RESEARCH_DISCOVERY ('researcher' vs 'research')
2. Programming action verb coverage ('handle', 'configure', 'integrate')
3. DOCUMENT_QUERY source enforcement with populated vs empty available_docs
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath("."))

from core.planner.enums import (
    EducationalIntent,
    DocumentUsageMode,
    SourceStrategy,
)
from core.models.domain import SourceType
from core.planner.rules import RuleBasedPlannerEngine


def test_1_handle_database_transactions_django():
    plan = RuleBasedPlannerEngine.generate_plan("How to handle database transactions in Django?", available_docs=[])
    assert plan.intent == EducationalIntent.PROGRAMMING_HELP


def test_2_configure_authentication_fastapi():
    plan = RuleBasedPlannerEngine.generate_plan("How to configure authentication in FastAPI?", available_docs=[])
    assert plan.intent == EducationalIntent.PROGRAMMING_HELP


def test_3_integrate_stripe_django():
    plan = RuleBasedPlannerEngine.generate_plan("How to integrate Stripe with Django?", available_docs=[])
    assert plan.intent == EducationalIntent.PROGRAMMING_HELP


def test_4_what_are_database_transactions():
    plan = RuleBasedPlannerEngine.generate_plan("What are database transactions?", available_docs=[])
    assert plan.intent == EducationalIntent.CONCEPT_EXPLANATION


def test_5_become_ai_researcher():
    plan = RuleBasedPlannerEngine.generate_plan("How do I become an AI researcher?", available_docs=[])
    assert plan.intent == EducationalIntent.CAREER_GUIDANCE


def test_6_transition_to_ai_researcher():
    plan = RuleBasedPlannerEngine.generate_plan("How do I transition from software engineer to AI researcher?", available_docs=[])
    assert plan.intent == EducationalIntent.CAREER_GUIDANCE


def test_7_recent_research_papers_rag():
    plan = RuleBasedPlannerEngine.generate_plan("Find recent research papers about RAG", available_docs=[])
    assert plan.intent == EducationalIntent.RESEARCH_DISCOVERY


def test_8_arxiv_research_vision_transformers():
    plan = RuleBasedPlannerEngine.generate_plan("Search arXiv for research on vision transformers", available_docs=[])
    assert plan.intent == EducationalIntent.RESEARCH_DISCOVERY


def test_9_document_query_populated_available_docs():
    plan = RuleBasedPlannerEngine.generate_plan("Compare the concepts in my PDF", available_docs=["concepts.pdf"])
    assert plan.intent == EducationalIntent.DOCUMENT_QUERY
    assert plan.document_usage_mode == DocumentUsageMode.REQUIRED
    assert SourceType.INTERNAL_DOCUMENT in plan.selected_sources


def test_10_document_query_empty_available_docs():
    plan = RuleBasedPlannerEngine.generate_plan("Compare the concepts in my PDF", available_docs=[])
    assert plan.intent == EducationalIntent.DOCUMENT_QUERY
    assert plan.document_usage_mode == DocumentUsageMode.OPTIONAL
    assert SourceType.INTERNAL_DOCUMENT not in plan.selected_sources


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
