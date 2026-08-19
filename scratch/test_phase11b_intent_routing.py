"""
EKIP Phase 11B — Intent Routing Precision & Planner Stabilization Test Suite.

Verifies intent classification precision across 23 primary test cases + 5 adversarial precedence tests.
Runs synchronously with zero network access or LLM dependency.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath("."))

from core.planner.enums import EducationalIntent
from core.planner.rules import RuleBasedPlannerEngine


TEST_SCENARIOS = [
    # Primary Phase 11B Scenarios
    (1, "What is object-oriented programming?", EducationalIntent.CONCEPT_EXPLANATION),
    (2, "What is OOP in Python?", EducationalIntent.CONCEPT_EXPLANATION),
    (3, "Explain list comprehensions in Python.", EducationalIntent.CONCEPT_EXPLANATION),
    (4, "What is the GIL in Python?", EducationalIntent.CONCEPT_EXPLANATION),
    (5, "Write a Python script to reverse a linked list.", EducationalIntent.PROGRAMMING_HELP),
    (6, "How to fix IndexError in Python?", EducationalIntent.PROGRAMMING_HELP),
    (7, "Implement a REST API endpoint using Django.", EducationalIntent.PROGRAMMING_HELP),
    (8, "Explain how to implement JWT authentication in Django.", EducationalIntent.PROGRAMMING_HELP),
    (9, "What is Django?", EducationalIntent.CONCEPT_EXPLANATION),
    (10, "Recommend YouTube videos for learning Docker.", EducationalIntent.VIDEO_RECOMMENDATION),
    (11, "Find a tutorial video explaining Transformer architecture.", EducationalIntent.VIDEO_RECOMMENDATION),
    (12, "Show me good GitHub repositories for learning RAG.", EducationalIntent.CODE_RESOURCE_RECOMMENDATION),
    (13, "Find an open-source implementation of an LLM agent in Python.", EducationalIntent.CODE_RESOURCE_RECOMMENDATION),
    (14, "Find recent research papers about RAG.", EducationalIntent.RESEARCH_DISCOVERY),
    (15, "Summarize my uploaded document.", EducationalIntent.DOCUMENT_QUERY),
    (16, "What does my file say about neural networks?", EducationalIntent.DOCUMENT_QUERY),
    (17, "Compare PyTorch vs TensorFlow.", EducationalIntent.COMPARISON),
    (18, "Create a practice quiz on Python basics.", EducationalIntent.PRACTICE_QUIZ),
    (19, "Generate study notes for Operating Systems.", EducationalIntent.STUDY_NOTES),
    (20, "Create flashcards for machine learning concepts.", EducationalIntent.FLASHCARDS),
    (21, "What are common interview questions for a Python developer?", EducationalIntent.INTERVIEW_PREPARATION),
    (22, "How do I become a Machine Learning Engineer?", EducationalIntent.CAREER_GUIDANCE),
    (23, "Provide a learning roadmap for full-stack development.", EducationalIntent.ROADMAP),

    # 5 Adversarial Precedence Tests
    (24, "Explain Python interview questions.", EducationalIntent.INTERVIEW_PREPARATION),
    (25, "Find a GitHub repository explaining Python.", EducationalIntent.CODE_RESOURCE_RECOMMENDATION),
    (26, "Summarize my Python document.", EducationalIntent.DOCUMENT_QUERY),
    (27, "How do I become a Python developer?", EducationalIntent.CAREER_GUIDANCE),
    (28, "Explain how to debug a Django application.", EducationalIntent.PROGRAMMING_HELP),
]


@pytest.mark.parametrize("test_id, query, expected_intent", TEST_SCENARIOS)
def test_phase11b_intent_routing_precision(test_id, query, expected_intent):
    plan = RuleBasedPlannerEngine.generate_plan(query, available_docs=[])
    assert plan.intent == expected_intent, (
        f"Test {test_id} failed for query '{query}': "
        f"Expected {expected_intent.name}, got {plan.intent.name}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
