"""
EKIP Planner Enum Consistency & Regression Test Suite.

Verifies that every EducationalIntent enum member referenced in rule engines exists,
ensures enum value uniqueness, and validates query execution against AttributeError regressions.
"""

import ast
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath("."))

from core.planner.enums import (
    EducationalIntent,
    DifficultyLevel,
    SourceStrategy,
    RetrievalStrategy,
    ExpectedOutputFormat,
    DocumentUsageMode,
)
from core.planner.rules import RuleBasedPlannerEngine


def test_ast_educational_intent_references():
    """Verify that all EducationalIntent attribute references in planner code exist in EducationalIntent enum."""
    rules_file_path = os.path.join("core", "planner", "rules.py")
    assert os.path.exists(rules_file_path), f"Planner rules file not found at {rules_file_path}"

    with open(rules_file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=rules_file_path)

    valid_intents = set(EducationalIntent.__members__.keys())
    missing_intents = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "EducationalIntent":
            if node.attr not in valid_intents:
                missing_intents.append((node.lineno, node.attr))

    if missing_intents:
        missing_str = ", ".join([f"Line {line}: {attr}" for line, attr in missing_intents])
        pytest.fail(f"Missing EducationalIntent enum member: {missing_str}")


def test_enum_value_uniqueness():
    """Verify that all EducationalIntent enum members have unique string values (no ambiguous aliases)."""
    values = [item.value for item in EducationalIntent]
    unique_values = set(values)
    assert len(values) == len(unique_values), f"Duplicate EducationalIntent values detected: {values}"


def test_query_oops_concept_execution():
    """Verify that 'what is oops concept in python' executes without AttributeError."""
    query = "what is oops concept in python"
    plan = RuleBasedPlannerEngine.generate_plan(query, available_docs=[])

    assert plan is not None
    assert hasattr(plan, "intent")
    assert isinstance(plan.intent, EducationalIntent)
    assert plan.intent in (EducationalIntent.PROGRAMMING_HELP, EducationalIntent.CONCEPT_EXPLANATION)
    assert plan.selected_sources is not None
    assert len(plan.selected_sources) > 0


def test_tutorial_queries_routing():
    """Verify that tutorial-seeking queries map cleanly to VIDEO_RECOMMENDATION or CODE_RESOURCE_RECOMMENDATION."""
    # Video tutorial query
    plan_video = RuleBasedPlannerEngine.generate_plan("python tutorial video", available_docs=[])
    assert plan_video.intent == EducationalIntent.VIDEO_RECOMMENDATION

    # Code resource tutorial query
    plan_code = RuleBasedPlannerEngine.generate_plan("python github repository tutorial code", available_docs=[])
    assert plan_code.intent in (EducationalIntent.CODE_RESOURCE_RECOMMENDATION, EducationalIntent.PROGRAMMING_HELP)


if __name__ == "__main__":
    test_ast_educational_intent_references()
    test_enum_value_uniqueness()
    test_query_oops_concept_execution()
    test_tutorial_queries_routing()
    print("ALL PLANNER ENUM CONSISTENCY TESTS PASSED SUCCESSFULLY!")
