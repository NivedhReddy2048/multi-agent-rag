"""
EKIP Phase 11F — Focused Refactor Intent Classification Regression Test.

Verifies:
1. Imperative/action refactoring requests route to PROGRAMMING_HELP.
2. Conceptual refactoring questions route to CONCEPT_EXPLANATION.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath("."))

from core.planner.enums import EducationalIntent
from core.planner.rules import RuleBasedPlannerEngine


def test_1_refactor_this_function_for_better_performance():
    plan = RuleBasedPlannerEngine.generate_plan("Refactor this function for better performance.", available_docs=[])
    assert plan.intent == EducationalIntent.PROGRAMMING_HELP


def test_2_can_you_refactor_this_python_code():
    plan = RuleBasedPlannerEngine.generate_plan("Can you refactor this Python code?", available_docs=[])
    assert plan.intent == EducationalIntent.PROGRAMMING_HELP


def test_3_how_should_i_refactor_this_function():
    plan = RuleBasedPlannerEngine.generate_plan("How should I refactor this function?", available_docs=[])
    assert plan.intent == EducationalIntent.PROGRAMMING_HELP


def test_4_what_is_refactoring():
    plan = RuleBasedPlannerEngine.generate_plan("What is refactoring?", available_docs=[])
    assert plan.intent == EducationalIntent.CONCEPT_EXPLANATION


def test_5_explain_code_refactoring():
    plan = RuleBasedPlannerEngine.generate_plan("Explain code refactoring.", available_docs=[])
    assert plan.intent == EducationalIntent.CONCEPT_EXPLANATION


def test_6_define_refactoring_in_software_engineering():
    plan = RuleBasedPlannerEngine.generate_plan("Define refactoring in software engineering.", available_docs=[])
    assert plan.intent == EducationalIntent.CONCEPT_EXPLANATION


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
