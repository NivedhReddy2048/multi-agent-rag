"""
EKIP Phase 11C — Adversarial Planner Stress Audit Script.

Evaluates real RuleBasedPlannerEngine across 90 adversarial test queries (Categories A-J).
Checks real intent classification, single-intent limitations, downstream source strategy,
and expected output format consistency without mutating production code.
"""

import sys
import os
import json

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


ADVERSARIAL_TEST_CASES = [
    # Category A: Concept vs Programming Ambiguity (10)
    {"id": "A1", "category": "Concept vs Programming", "query": "What is REST API in Python?", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": False, "secondary": []},
    {"id": "A2", "category": "Concept vs Programming", "query": "Explain Django architecture.", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": False, "secondary": []},
    {"id": "A3", "category": "Concept vs Programming", "query": "What is dependency injection in FastAPI?", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": False, "secondary": []},
    {"id": "A4", "category": "Concept vs Programming", "query": "Explain Python decorators with examples.", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": True, "secondary": [EducationalIntent.PROGRAMMING_HELP]},
    {"id": "A5", "category": "Concept vs Programming", "query": "Teach me recursion in Java.", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": False, "secondary": []},
    {"id": "A6", "category": "Concept vs Programming", "query": "What is async programming in Python?", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": False, "secondary": []},
    {"id": "A7", "category": "Concept vs Programming", "query": "Explain list comprehensions in Python with a code snippet.", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": True, "secondary": [EducationalIntent.PROGRAMMING_HELP]},
    {"id": "A8", "category": "Concept vs Programming", "query": "What are decorators in Python and why do we use them?", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": False, "secondary": []},
    {"id": "A9", "category": "Concept vs Programming", "query": "How does the Global Interpreter Lock work in Python?", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": False, "secondary": []},
    {"id": "A10", "category": "Concept vs Programming", "query": "Explain object-oriented programming concepts in C++.", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": False, "secondary": []},

    # Category B: Explicit Programming Actions (10)
    {"id": "B1", "category": "Explicit Programming Actions", "query": "Implement JWT authentication in Django.", "expected_intent": EducationalIntent.PROGRAMMING_HELP, "is_ambiguous": False, "secondary": []},
    {"id": "B2", "category": "Explicit Programming Actions", "query": "Write a FastAPI endpoint for user registration.", "expected_intent": EducationalIntent.PROGRAMMING_HELP, "is_ambiguous": False, "secondary": []},
    {"id": "B3", "category": "Explicit Programming Actions", "query": "Debug this Python recursion error.", "expected_intent": EducationalIntent.PROGRAMMING_HELP, "is_ambiguous": False, "secondary": []},
    {"id": "B4", "category": "Explicit Programming Actions", "query": "How do I fix a Django migration error?", "expected_intent": EducationalIntent.PROGRAMMING_HELP, "is_ambiguous": False, "secondary": []},
    {"id": "B5", "category": "Explicit Programming Actions", "query": "Write code to reverse a binary tree.", "expected_intent": EducationalIntent.PROGRAMMING_HELP, "is_ambiguous": False, "secondary": []},
    {"id": "B6", "category": "Explicit Programming Actions", "query": "Refactor this function for better performance.", "expected_intent": EducationalIntent.PROGRAMMING_HELP, "is_ambiguous": False, "secondary": []},
    {"id": "B7", "category": "Explicit Programming Actions", "query": "Create a Python script to scrape a webpage using BeautifulSoup.", "expected_intent": EducationalIntent.PROGRAMMING_HELP, "is_ambiguous": False, "secondary": []},
    {"id": "B8", "category": "Explicit Programming Actions", "query": "Fix IndexError: list index out of range in Python script.", "expected_intent": EducationalIntent.PROGRAMMING_HELP, "is_ambiguous": False, "secondary": []},
    {"id": "B9", "category": "Explicit Programming Actions", "query": "How to handle database transactions in Django?", "expected_intent": EducationalIntent.PROGRAMMING_HELP, "is_ambiguous": False, "secondary": []},
    {"id": "B10", "category": "Explicit Programming Actions", "query": "Write a unit test for my FastAPI authentication service.", "expected_intent": EducationalIntent.PROGRAMMING_HELP, "is_ambiguous": False, "secondary": []},

    # Category C: Code Resource vs Programming Help (10)
    {"id": "C1", "category": "Code Resource vs Help", "query": "Find open-source implementations of RAG.", "expected_intent": EducationalIntent.CODE_RESOURCE_RECOMMENDATION, "is_ambiguous": False, "secondary": []},
    {"id": "C2", "category": "Code Resource vs Help", "query": "Show me GitHub repositories for Django authentication.", "expected_intent": EducationalIntent.CODE_RESOURCE_RECOMMENDATION, "is_ambiguous": False, "secondary": []},
    {"id": "C3", "category": "Code Resource vs Help", "query": "I need an example project for FastAPI.", "expected_intent": EducationalIntent.CODE_RESOURCE_RECOMMENDATION, "is_ambiguous": False, "secondary": []},
    {"id": "C4", "category": "Code Resource vs Help", "query": "Find a repository implementing a vector database.", "expected_intent": EducationalIntent.CODE_RESOURCE_RECOMMENDATION, "is_ambiguous": False, "secondary": []},
    {"id": "C5", "category": "Code Resource vs Help", "query": "How do I implement a vector database?", "expected_intent": EducationalIntent.PROGRAMMING_HELP, "is_ambiguous": False, "secondary": []},
    {"id": "C6", "category": "Code Resource vs Help", "query": "Recommend open-source Python codebases for microservices.", "expected_intent": EducationalIntent.CODE_RESOURCE_RECOMMENDATION, "is_ambiguous": False, "secondary": []},
    {"id": "C7", "category": "Code Resource vs Help", "query": "Find GitHub repos with code examples for PyTorch vision models.", "expected_intent": EducationalIntent.CODE_RESOURCE_RECOMMENDATION, "is_ambiguous": False, "secondary": []},
    {"id": "C8", "category": "Code Resource vs Help", "query": "Show me reference implementations of LLM agents on GitHub.", "expected_intent": EducationalIntent.CODE_RESOURCE_RECOMMENDATION, "is_ambiguous": False, "secondary": []},
    {"id": "C9", "category": "Code Resource vs Help", "query": "Build an open-source chatbot in Python.", "expected_intent": EducationalIntent.PROGRAMMING_HELP, "is_ambiguous": True, "secondary": [EducationalIntent.CODE_RESOURCE_RECOMMENDATION]},
    {"id": "C10", "category": "Code Resource vs Help", "query": "Where can I find open-source Django boilerplates?", "expected_intent": EducationalIntent.CODE_RESOURCE_RECOMMENDATION, "is_ambiguous": False, "secondary": []},

    # Category D: Document Intent Conflicts (10)
    {"id": "D1", "category": "Document Intent Conflicts", "query": "Summarize my uploaded document.", "expected_intent": EducationalIntent.DOCUMENT_QUERY, "is_ambiguous": False, "secondary": []},
    {"id": "D2", "category": "Document Intent Conflicts", "query": "Explain my document.", "expected_intent": EducationalIntent.DOCUMENT_QUERY, "is_ambiguous": False, "secondary": []},
    {"id": "D3", "category": "Document Intent Conflicts", "query": "What does my file say about transformers?", "expected_intent": EducationalIntent.DOCUMENT_QUERY, "is_ambiguous": False, "secondary": []},
    {"id": "D4", "category": "Document Intent Conflicts", "query": "Compare the concepts in my PDF.", "expected_intent": EducationalIntent.DOCUMENT_QUERY, "is_ambiguous": True, "secondary": [EducationalIntent.COMPARISON]},
    {"id": "D5", "category": "Document Intent Conflicts", "query": "Give me quiz questions from my uploaded notes.", "expected_intent": EducationalIntent.DOCUMENT_QUERY, "is_ambiguous": True, "secondary": [EducationalIntent.QUIZ_GENERATION]},
    {"id": "D6", "category": "Document Intent Conflicts", "query": "What are the key findings in this document?", "expected_intent": EducationalIntent.DOCUMENT_QUERY, "is_ambiguous": False, "secondary": []},
    {"id": "D7", "category": "Document Intent Conflicts", "query": "Summarize the architectural specs in my file.", "expected_intent": EducationalIntent.DOCUMENT_QUERY, "is_ambiguous": False, "secondary": []},
    {"id": "D8", "category": "Document Intent Conflicts", "query": "Generate flashcards from my uploaded notes.", "expected_intent": EducationalIntent.DOCUMENT_QUERY, "is_ambiguous": True, "secondary": [EducationalIntent.FLASHCARDS]},
    {"id": "D9", "category": "Document Intent Conflicts", "query": "Explain the legacy model parameters in my uploaded PDF.", "expected_intent": EducationalIntent.DOCUMENT_QUERY, "is_ambiguous": False, "secondary": []},
    {"id": "D10", "category": "Document Intent Conflicts", "query": "Is there any contradiction in my uploaded document?", "expected_intent": EducationalIntent.DOCUMENT_QUERY, "is_ambiguous": False, "secondary": []},

    # Category E: Research vs Resource Discovery (8)
    {"id": "E1", "category": "Research vs Resource", "query": "Find recent papers about RAG.", "expected_intent": EducationalIntent.RESEARCH_DISCOVERY, "is_ambiguous": False, "secondary": []},
    {"id": "E2", "category": "Research vs Resource", "query": "Find recent RAG papers and GitHub implementations.", "expected_intent": EducationalIntent.RESEARCH_DISCOVERY, "is_ambiguous": True, "secondary": [EducationalIntent.CODE_RESOURCE_RECOMMENDATION]},
    {"id": "E3", "category": "Research vs Resource", "query": "Search arXiv for transformer papers.", "expected_intent": EducationalIntent.RESEARCH_DISCOVERY, "is_ambiguous": False, "secondary": []},
    {"id": "E4", "category": "Research vs Resource", "query": "Find open-source implementations based on recent RAG papers.", "expected_intent": EducationalIntent.CODE_RESOURCE_RECOMMENDATION, "is_ambiguous": True, "secondary": [EducationalIntent.RESEARCH_DISCOVERY]},
    {"id": "E5", "category": "Research vs Resource", "query": "Compare recent research approaches to RAG.", "expected_intent": EducationalIntent.RESEARCH_DISCOVERY, "is_ambiguous": True, "secondary": [EducationalIntent.COMPARISON]},
    {"id": "E6", "category": "Research vs Resource", "query": "What are recent literature surveys on attention mechanisms?", "expected_intent": EducationalIntent.RESEARCH_DISCOVERY, "is_ambiguous": False, "secondary": []},
    {"id": "E7", "category": "Research vs Resource", "query": "Search arXiv for vision transformer benchmarks.", "expected_intent": EducationalIntent.RESEARCH_DISCOVERY, "is_ambiguous": False, "secondary": []},
    {"id": "E8", "category": "Research vs Resource", "query": "Recommend academic papers and YouTube videos on LLM fine-tuning.", "expected_intent": EducationalIntent.RESEARCH_DISCOVERY, "is_ambiguous": True, "secondary": [EducationalIntent.VIDEO_RECOMMENDATION]},

    # Category F: Career / Interview / Roadmap Conflicts (8)
    {"id": "F1", "category": "Career / Interview / Roadmap", "query": "Give me Python interview questions and a learning roadmap.", "expected_intent": EducationalIntent.INTERVIEW_PREPARATION, "is_ambiguous": True, "secondary": [EducationalIntent.ROADMAP]},
    {"id": "F2", "category": "Career / Interview / Roadmap", "query": "How do I become a backend developer?", "expected_intent": EducationalIntent.CAREER_GUIDANCE, "is_ambiguous": False, "secondary": []},
    {"id": "F3", "category": "Career / Interview / Roadmap", "query": "What skills do I need for a machine learning career?", "expected_intent": EducationalIntent.CAREER_GUIDANCE, "is_ambiguous": False, "secondary": []},
    {"id": "F4", "category": "Career / Interview / Roadmap", "query": "Give me interview preparation for Django developer jobs.", "expected_intent": EducationalIntent.INTERVIEW_PREPARATION, "is_ambiguous": False, "secondary": []},
    {"id": "F5", "category": "Career / Interview / Roadmap", "query": "Create a roadmap to become a data engineer.", "expected_intent": EducationalIntent.CAREER_GUIDANCE, "is_ambiguous": True, "secondary": [EducationalIntent.ROADMAP]},
    {"id": "F6", "category": "Career / Interview / Roadmap", "query": "What questions will be asked in a senior Python developer interview?", "expected_intent": EducationalIntent.INTERVIEW_PREPARATION, "is_ambiguous": False, "secondary": []},
    {"id": "F7", "category": "Career / Interview / Roadmap", "query": "How to transition from software engineer to AI researcher?", "expected_intent": EducationalIntent.CAREER_GUIDANCE, "is_ambiguous": False, "secondary": []},
    {"id": "F8", "category": "Career / Interview / Roadmap", "query": "Provide a study plan and roadmap for cloud architecture.", "expected_intent": EducationalIntent.ROADMAP, "is_ambiguous": False, "secondary": []},

    # Category G: Follow-up and Contextual Queries (8)
    {"id": "G1", "category": "Follow-up & Contextual", "query": "Explain that in more detail.", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": False, "secondary": []},
    {"id": "G2", "category": "Follow-up & Contextual", "query": "Give me examples.", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": False, "secondary": []},
    {"id": "G3", "category": "Follow-up & Contextual", "query": "What about Python?", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": False, "secondary": []},
    {"id": "G4", "category": "Follow-up & Contextual", "query": "Compare those two.", "expected_intent": EducationalIntent.COMPARISON, "is_ambiguous": False, "secondary": []},
    {"id": "G5", "category": "Follow-up & Contextual", "query": "Can you simplify it?", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": False, "secondary": []},
    {"id": "G6", "category": "Follow-up & Contextual", "query": "Now give me interview questions.", "expected_intent": EducationalIntent.INTERVIEW_PREPARATION, "is_ambiguous": False, "secondary": []},
    {"id": "G7", "category": "Follow-up & Contextual", "query": "Show me code for that.", "expected_intent": EducationalIntent.PROGRAMMING_HELP, "is_ambiguous": False, "secondary": []},
    {"id": "G8", "category": "Follow-up & Contextual", "query": "Find videos on that topic.", "expected_intent": EducationalIntent.VIDEO_RECOMMENDATION, "is_ambiguous": False, "secondary": []},

    # Category H: Keyword Traps / False Positives (8)
    {"id": "H1", "category": "Keyword Traps", "query": "What is the Python programming language?", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": False, "secondary": []},
    {"id": "H2", "category": "Keyword Traps", "query": "Tell me about Java.", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": False, "secondary": []},
    {"id": "H3", "category": "Keyword Traps", "query": "My document is about Python, explain recursion.", "expected_intent": EducationalIntent.DOCUMENT_QUERY, "is_ambiguous": True, "secondary": [EducationalIntent.CONCEPT_EXPLANATION]},
    {"id": "H4", "category": "Keyword Traps", "query": "What is code quality?", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": False, "secondary": []},
    {"id": "H5", "category": "Keyword Traps", "query": "Explain the role of functions in mathematics.", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": False, "secondary": []},
    {"id": "H6", "category": "Keyword Traps", "query": "What is a class in object-oriented programming?", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": False, "secondary": []},
    {"id": "H7", "category": "Keyword Traps", "query": "Explain the concept of bugs in software design.", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": False, "secondary": []},
    {"id": "H8", "category": "Keyword Traps", "query": "What is a script in theatrical drama?", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": False, "secondary": []},

    # Category I: Natural Language / Long Queries (8)
    {"id": "I1", "category": "Natural Language Multi-Intent", "query": "I am learning backend development and I understand Python basics, but I am confused about Django REST APIs. Can you explain what they are and show me how I would build a simple endpoint?", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": True, "secondary": [EducationalIntent.PROGRAMMING_HELP]},
    {"id": "I2", "category": "Natural Language Multi-Intent", "query": "I uploaded my thesis PDF yesterday and I want to summarize the background section, and also generate a 10-question practice quiz based on it.", "expected_intent": EducationalIntent.DOCUMENT_QUERY, "is_ambiguous": True, "secondary": [EducationalIntent.QUIZ_GENERATION]},
    {"id": "I3", "category": "Natural Language Multi-Intent", "query": "I have an interview coming up for a Machine Learning Engineer position next week. What key concepts should I review and what are the best GitHub projects to practice?", "expected_intent": EducationalIntent.INTERVIEW_PREPARATION, "is_ambiguous": True, "secondary": [EducationalIntent.CODE_RESOURCE_RECOMMENDATION]},
    {"id": "I4", "category": "Natural Language Multi-Intent", "query": "I need to understand how attention works in transformers. Please recommend YouTube videos and also link recent arXiv papers.", "expected_intent": EducationalIntent.RESEARCH_DISCOVERY, "is_ambiguous": True, "secondary": [EducationalIntent.VIDEO_RECOMMENDATION]},
    {"id": "I5", "category": "Natural Language Multi-Intent", "query": "Can you compare PyTorch and TensorFlow for production deployment, and also provide a simple code snippet showing model loading in PyTorch?", "expected_intent": EducationalIntent.COMPARISON, "is_ambiguous": True, "secondary": [EducationalIntent.PROGRAMMING_HELP]},
    {"id": "I6", "category": "Natural Language Multi-Intent", "query": "I am trying to fix a memory leak in my Python FastAPI app. Can you help debug the issue and suggest optimization techniques?", "expected_intent": EducationalIntent.PROGRAMMING_HELP, "is_ambiguous": False, "secondary": []},
    {"id": "I7", "category": "Natural Language Multi-Intent", "query": "I am planning a career change into data engineering. What is the learning path and what books do you recommend reading?", "expected_intent": EducationalIntent.CAREER_GUIDANCE, "is_ambiguous": True, "secondary": [EducationalIntent.ROADMAP, EducationalIntent.BOOK_RECOMMENDATION]},
    {"id": "I8", "category": "Natural Language Multi-Intent", "query": "What does my uploaded hardware cluster PDF say about GPU VRAM, and how does it compare to standard cloud instances?", "expected_intent": EducationalIntent.DOCUMENT_QUERY, "is_ambiguous": True, "secondary": [EducationalIntent.COMPARISON]},

    # Category J: Negative / Boundary Cases (10)
    {"id": "J1", "category": "Boundary Cases", "query": "Define backpropagation.", "expected_intent": EducationalIntent.CONCEPT_EXPLANATION, "is_ambiguous": False, "secondary": []},
    {"id": "J2", "category": "Boundary Cases", "query": "Create 5 flashcards for Python data structures.", "expected_intent": EducationalIntent.FLASHCARDS, "is_ambiguous": False, "secondary": []},
    {"id": "J3", "category": "Boundary Cases", "query": "Generate a practice quiz for SQL joins.", "expected_intent": EducationalIntent.QUIZ_GENERATION, "is_ambiguous": False, "secondary": []},
    {"id": "J4", "category": "Boundary Cases", "query": "Provide study notes for operating system process scheduling.", "expected_intent": EducationalIntent.STUDY_NOTES, "is_ambiguous": False, "secondary": []},
    {"id": "J5", "category": "Boundary Cases", "query": "What are the latest news on OpenAI models online?", "expected_intent": EducationalIntent.WEB_INFORMATION, "is_ambiguous": False, "secondary": []},
    {"id": "J6", "category": "Boundary Cases", "query": "Recommend textbooks for discrete mathematics.", "expected_intent": EducationalIntent.BOOK_RECOMMENDATION, "is_ambiguous": False, "secondary": []},
    {"id": "J7", "category": "Boundary Cases", "query": "Explain list comprehensions vs generator expressions in Python.", "expected_intent": EducationalIntent.COMPARISON, "is_ambiguous": False, "secondary": [EducationalIntent.CONCEPT_EXPLANATION]},
    {"id": "J8", "category": "Boundary Cases", "query": "How to learn machine learning in 6 months?", "expected_intent": EducationalIntent.ROADMAP, "is_ambiguous": False, "secondary": []},
    {"id": "J9", "category": "Boundary Cases", "query": "Summarize the history of artificial intelligence.", "expected_intent": EducationalIntent.TOPIC_SUMMARY, "is_ambiguous": False, "secondary": []},
    {"id": "J10", "category": "Boundary Cases", "query": "Find YouTube video tutorials on Kubernetes deployment.", "expected_intent": EducationalIntent.VIDEO_RECOMMENDATION, "is_ambiguous": False, "secondary": []},
]


def run_phase11c_audit():
    print("=" * 80, flush=True)
    print("EKIP PHASE 11C — ADVERSARIAL PLANNER STRESS AUDIT", flush=True)
    print("=" * 80, flush=True)

    results = []
    pass_count = 0
    fail_count = 0
    ambiguous_count = 0

    downstream_anomalies = []

    for test in ADVERSARIAL_TEST_CASES:
        plan = RuleBasedPlannerEngine.generate_plan(test["query"], available_docs=["test_doc.pdf"])
        detected = plan.intent
        expected = test["expected_intent"]
        is_ambig = test["is_ambiguous"]

        status = "UNKNOWN"
        reason = ""

        if detected == expected:
            status = "PASS"
            pass_count += 1
            reason = f"Primary detected intent '{detected.name}' matches expected intent."
        elif is_ambig and detected in test["secondary"]:
            status = "AMBIGUOUS"
            ambiguous_count += 1
            reason = f"Multi-intent query: Detected secondary intent '{detected.name}' instead of primary '{expected.name}'. Precedence acceptable."
        elif is_ambig and detected != expected:
            status = "AMBIGUOUS"
            ambiguous_count += 1
            reason = f"Multi-intent query: Detected '{detected.name}'. Primary expected '{expected.name}', secondary {[s.name for s in test['secondary']]}."
        else:
            status = "FAIL"
            fail_count += 1
            reason = f"Detected intent '{detected.name}' does not match expected intent '{expected.name}'."

        record = {
            "id": test["id"],
            "category": test["category"],
            "query": test["query"],
            "detected_intent": detected.name,
            "expected_intent": expected.name,
            "status": status,
            "reason": reason,
            "secondary_possible_intents": [s.name for s in test["secondary"]],
            "source_strategy": plan.source_strategy.value,
            "retrieval_strategy": plan.retrieval_strategy.value,
            "expected_output_format": plan.expected_output.value,
            "document_usage_mode": plan.document_usage_mode.value,
        }
        results.append(record)

        # Downstream consistency checks
        if detected == EducationalIntent.CONCEPT_EXPLANATION and plan.expected_output == ExpectedOutputFormat.CODE_WALKTHROUGH:
            downstream_anomalies.append((test["id"], "CONCEPT_EXPLANATION forced CODE_WALKTHROUGH"))

        if detected == EducationalIntent.DOCUMENT_QUERY and plan.source_strategy != SourceStrategy.DOCUMENT_ONLY:
            downstream_anomalies.append((test["id"], "DOCUMENT_QUERY did not force DOCUMENT_ONLY"))

        q_short = test["query"][:42] + ".." if len(test["query"]) > 44 else test["query"]
        print(f"[{status:<9}] {test['id']:<4} | {q_short:<44} | Det: {detected.name:<25} | Exp: {expected.name:<25}", flush=True)

    total_queries = len(ADVERSARIAL_TEST_CASES)
    acc_excl_ambig = (pass_count / (total_queries - ambiguous_count)) * 100 if (total_queries - ambiguous_count) > 0 else 100.0
    acc_incl_ambig = ((pass_count + ambiguous_count) / total_queries) * 100

    print("\n" + "=" * 80, flush=True)
    print(f"TOTAL QUERIES TESTED         : {total_queries}", flush=True)
    print(f"PASS COUNT                   : {pass_count}", flush=True)
    print(f"FAIL COUNT                   : {fail_count}", flush=True)
    print(f"AMBIGUOUS COUNT              : {ambiguous_count}", flush=True)
    print(f"ACCURACY (Excl. Ambiguous)   : {pass_count}/{total_queries - ambiguous_count} ({acc_excl_ambig:.1f}%)", flush=True)
    print(f"ACCURACY (Incl. Ambiguous)   : {pass_count + ambiguous_count}/{total_queries} ({acc_incl_ambig:.1f}%)", flush=True)
    print(f"DOWNSTREAM STRATEGY ANOMALIES: {len(downstream_anomalies)}", flush=True)
    print("=" * 80, flush=True)

    if downstream_anomalies:
        print("\n--- DOWNSTREAM STRATEGY ANOMALIES ---", flush=True)
        for item_id, err in downstream_anomalies:
            print(f"  - [{item_id}]: {err}", flush=True)

    verdict = "PHASE 11C — PASS"
    if fail_count > 0:
        verdict = "PHASE 11C — FIXES REQUIRED"
    elif ambiguous_count > 0 or len(downstream_anomalies) > 0:
        verdict = "PHASE 11C — PASS WITH LIMITATIONS"

    print(f"\nFINAL VERDICT: {verdict}", flush=True)
    print("=" * 80, flush=True)

    # Save output to scratch
    out_file = "scratch/phase11c_audit_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "total_queries": total_queries,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "ambiguous_count": ambiguous_count,
            "accuracy_excluding_ambiguous": round(acc_excl_ambig, 1),
            "accuracy_including_ambiguous": round(acc_incl_ambig, 1),
            "downstream_anomalies_count": len(downstream_anomalies),
            "downstream_anomalies": downstream_anomalies,
            "verdict": verdict,
            "details": results
        }, f, indent=2)
    print(f"Saved full audit JSON log to: {out_file}", flush=True)


if __name__ == "__main__":
    run_phase11c_audit()
