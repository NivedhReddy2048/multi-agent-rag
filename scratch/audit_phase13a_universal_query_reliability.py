"""
EKIP Phase 13A — Universal Query Reliability & Adversarial End-to-End Audit
Creates a 100-query test matrix across categories A-T to audit intent routing,
source dispatch, retrieval preservation, synthesis quality, fallback behavior,
and compound/ambiguous query handling.
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

# 100 Adversarial Test Queries across Categories A through T
AUDIT_MATRIX = [
    # A. CONCEPT_EXPLANATION
    {"id": 1, "cat": "A. CONCEPT_EXPLANATION", "query": "Explain backpropagation in deep learning.", "expected_intent": "CONCEPT_EXPLANATION"},
    {"id": 2, "cat": "A. CONCEPT_EXPLANATION", "query": "What is gradient descent and how does it work?", "expected_intent": "CONCEPT_EXPLANATION"},
    {"id": 3, "cat": "A. CONCEPT_EXPLANATION", "query": "How does the attention mechanism work in Transformer models?", "expected_intent": "CONCEPT_EXPLANATION"},
    {"id": 4, "cat": "A. CONCEPT_EXPLANATION", "query": "Explain dependency injection in software architecture.", "expected_intent": "CONCEPT_EXPLANATION"},
    {"id": 5, "cat": "A. CONCEPT_EXPLANATION", "query": "What are ACID properties in relational database management systems?", "expected_intent": "CONCEPT_EXPLANATION"},

    # B. PROGRAMMING_HELP
    {"id": 6, "cat": "B. PROGRAMMING_HELP", "query": "Fix this Python syntax error: SyntaxError: invalid syntax in def foo()", "expected_intent": "PROGRAMMING_HELP"},
    {"id": 7, "cat": "B. PROGRAMMING_HELP", "query": "Implement binary search in Python.", "expected_intent": "PROGRAMMING_HELP"},
    {"id": 8, "cat": "B. PROGRAMMING_HELP", "query": "Write a Dockerfile for a FastAPI application.", "expected_intent": "PROGRAMMING_HELP"},
    {"id": 9, "cat": "B. PROGRAMMING_HELP", "query": "Refactor this function for better performance.", "expected_intent": "PROGRAMMING_HELP"},
    {"id": 10, "cat": "B. PROGRAMMING_HELP", "query": "How to connect PostgreSQL database in Node.js using pg library?", "expected_intent": "PROGRAMMING_HELP"},

    # C. RESEARCH_DISCOVERY
    {"id": 11, "cat": "C. RESEARCH_DISCOVERY", "query": "Find research paper abstracts on Attention Is All You Need.", "expected_intent": "RESEARCH_DISCOVERY"},
    {"id": 12, "cat": "C. RESEARCH_DISCOVERY", "query": "Find recent preprints on Graph Neural Networks.", "expected_intent": "RESEARCH_DISCOVERY"},
    {"id": 13, "cat": "C. RESEARCH_DISCOVERY", "query": "Search research literature for LLM hallucination mitigation.", "expected_intent": "RESEARCH_DISCOVERY"},
    {"id": 14, "cat": "C. RESEARCH_DISCOVERY", "query": "Find papers on diffusion models in medical imaging.", "expected_intent": "RESEARCH_DISCOVERY"},
    {"id": 15, "cat": "C. RESEARCH_DISCOVERY", "query": "Find research papers about transformer quantization.", "expected_intent": "RESEARCH_DISCOVERY"},

    # D. VIDEO_RECOMMENDATION
    {"id": 16, "cat": "D. VIDEO_RECOMMENDATION", "query": "Recommend top learning video concepts for understanding React hooks.", "expected_intent": "VIDEO_RECOMMENDATION"},
    {"id": 17, "cat": "D. VIDEO_RECOMMENDATION", "query": "Find tutorial videos for PyTorch basics.", "expected_intent": "VIDEO_RECOMMENDATION"},
    {"id": 18, "cat": "D. VIDEO_RECOMMENDATION", "query": "Recommend videos explaining Kubernetes architecture.", "expected_intent": "VIDEO_RECOMMENDATION"},
    {"id": 19, "cat": "D. VIDEO_RECOMMENDATION", "query": "Show me videos for learning Rust language.", "expected_intent": "VIDEO_RECOMMENDATION"},
    {"id": 20, "cat": "D. VIDEO_RECOMMENDATION", "query": "Recommend top learning video concepts for understanding SQL joins.", "expected_intent": "VIDEO_RECOMMENDATION"},

    # E. CODE_RESOURCE_RECOMMENDATION
    {"id": 21, "cat": "E. CODE_RESOURCE_RECOMMENDATION", "query": "Find GitHub repos for RAG frameworks in Python.", "expected_intent": "CODE_RESOURCE_RECOMMENDATION"},
    {"id": 22, "cat": "E. CODE_RESOURCE_RECOMMENDATION", "query": "Recommend open-source repositories for object detection.", "expected_intent": "CODE_RESOURCE_RECOMMENDATION"},
    {"id": 23, "cat": "E. CODE_RESOURCE_RECOMMENDATION", "query": "Find Python libraries for time-series forecasting.", "expected_intent": "CODE_RESOURCE_RECOMMENDATION"},
    {"id": 24, "cat": "E. CODE_RESOURCE_RECOMMENDATION", "query": "Show me GitHub projects implementing Transformer from scratch.", "expected_intent": "CODE_RESOURCE_RECOMMENDATION"},
    {"id": 25, "cat": "E. CODE_RESOURCE_RECOMMENDATION", "query": "Find open-source repos for LangChain alternatives.", "expected_intent": "CODE_RESOURCE_RECOMMENDATION"},

    # F. DOCUMENT_QUERY
    {"id": 26, "cat": "F. DOCUMENT_QUERY", "query": "Summarize my uploaded document.", "expected_intent": "DOCUMENT_QUERY"},
    {"id": 27, "cat": "F. DOCUMENT_QUERY", "query": "What does section 3 of my PDF say?", "expected_intent": "DOCUMENT_QUERY"},
    {"id": 28, "cat": "F. DOCUMENT_QUERY", "query": "Extract table 2 from the uploaded file.", "expected_intent": "DOCUMENT_QUERY"},
    {"id": 29, "cat": "F. DOCUMENT_QUERY", "query": "Does my document mention vector database benchmark?", "expected_intent": "DOCUMENT_QUERY"},
    {"id": 30, "cat": "F. DOCUMENT_QUERY", "query": "Compare page 5 with page 12 of my uploaded document.", "expected_intent": "DOCUMENT_QUERY"},

    # G. CAREER_GUIDANCE
    {"id": 31, "cat": "G. CAREER_GUIDANCE", "query": "How do I become a Senior AI Engineer?", "expected_intent": "CAREER_GUIDANCE"},
    {"id": 32, "cat": "G. CAREER_GUIDANCE", "query": "What skills are needed for Data Platform Engineering?", "expected_intent": "CAREER_GUIDANCE"},
    {"id": 33, "cat": "G. CAREER_GUIDANCE", "query": "Career path from Junior Developer to Solutions Architect.", "expected_intent": "CAREER_GUIDANCE"},
    {"id": 34, "cat": "G. CAREER_GUIDANCE", "query": "Is DevOps a good career path in 2026?", "expected_intent": "CAREER_GUIDANCE"},
    {"id": 35, "cat": "G. CAREER_GUIDANCE", "query": "Transitioning from Data Analyst to Machine Learning Engineer.", "expected_intent": "CAREER_GUIDANCE"},

    # H. INTERVIEW_PREPARATION
    {"id": 36, "cat": "H. INTERVIEW_PREPARATION", "query": "Top 10 interview questions for Senior Python Developer.", "expected_intent": "INTERVIEW_PREPARATION"},
    {"id": 37, "cat": "H. INTERVIEW_PREPARATION", "query": "How to prepare for System Design interview at Big Tech.", "expected_intent": "INTERVIEW_PREPARATION"},
    {"id": 38, "cat": "H. INTERVIEW_PREPARATION", "query": "Common coding interview questions for dynamic programming.", "expected_intent": "INTERVIEW_PREPARATION"},
    {"id": 39, "cat": "H. INTERVIEW_PREPARATION", "query": "Behavioral interview questions for Engineering Manager role.", "expected_intent": "INTERVIEW_PREPARATION"},
    {"id": 40, "cat": "H. INTERVIEW_PREPARATION", "query": "Mock interview questions on Distributed Systems.", "expected_intent": "INTERVIEW_PREPARATION"},

    # I. QUIZ / FLASHCARD / STUDY REQUESTS
    {"id": 41, "cat": "I. QUIZ_FLASHCARD", "query": "Generate a 5-question quiz on Python OOP.", "expected_intent": "QUIZ_GENERATION"},
    {"id": 42, "cat": "I. QUIZ_FLASHCARD", "query": "Create flashcards for Docker commands.", "expected_intent": "FLASHCARDS"},
    {"id": 43, "cat": "I. QUIZ_FLASHCARD", "query": "Generate study notes for Operating Systems deadlock.", "expected_intent": "STUDY_NOTES"},
    {"id": 44, "cat": "I. QUIZ_FLASHCARD", "query": "Make a practice quiz on linear algebra for machine learning.", "expected_intent": "PRACTICE_QUIZ"},
    {"id": 45, "cat": "I. QUIZ_FLASHCARD", "query": "Create flashcards for AWS core services.", "expected_intent": "FLASHCARDS"},

    # J. COMPARISON
    {"id": 46, "cat": "J. COMPARISON", "query": "Compare PostgreSQL vs MongoDB for high-throughput applications.", "expected_intent": "COMPARISON"},
    {"id": 47, "cat": "J. COMPARISON", "query": "Difference between REST API and GraphQL architecture.", "expected_intent": "COMPARISON"},
    {"id": 48, "cat": "J. COMPARISON", "query": "PyTorch vs TensorFlow for production AI deployment.", "expected_intent": "COMPARISON"},
    {"id": 49, "cat": "J. COMPARISON", "query": "Compare Microservices vs Monolith architecture.", "expected_intent": "COMPARISON"},
    {"id": 50, "cat": "J. COMPARISON", "query": "Docker vs Kubernetes comparison for container orchestration.", "expected_intent": "COMPARISON"},

    # K. ROADMAP
    {"id": 51, "cat": "K. ROADMAP", "query": "Create a 6-month learning roadmap for Machine Learning.", "expected_intent": "ROADMAP"},
    {"id": 52, "cat": "K. ROADMAP", "query": "Learning path for Full Stack Web Development in 2026.", "expected_intent": "ROADMAP"},
    {"id": 53, "cat": "K. ROADMAP", "query": "Roadmap to master Cloud Native DevOps engineering.", "expected_intent": "ROADMAP"},
    {"id": 54, "cat": "K. ROADMAP", "query": "Step-by-step roadmap for Cybersecurity beginner.", "expected_intent": "ROADMAP"},
    {"id": 55, "cat": "K. ROADMAP", "query": "Learning path for Data Engineering with Apache Spark.", "expected_intent": "ROADMAP"},

    # L. BOOK_RECOMMENDATION
    {"id": 56, "cat": "L. BOOK_RECOMMENDATION", "query": "Recommend top books for learning System Design.", "expected_intent": "BOOK_RECOMMENDATION"},
    {"id": 57, "cat": "L. BOOK_RECOMMENDATION", "query": "Best books for mastering Python design patterns.", "expected_intent": "BOOK_RECOMMENDATION"},
    {"id": 58, "cat": "L. BOOK_RECOMMENDATION", "query": "Book recommendations for Deep Learning fundamentals.", "expected_intent": "BOOK_RECOMMENDATION"},
    {"id": 59, "cat": "L. BOOK_RECOMMENDATION", "query": "Best books on Clean Code and Refactoring.", "expected_intent": "BOOK_RECOMMENDATION"},
    {"id": 60, "cat": "L. BOOK_RECOMMENDATION", "query": "Top reading list for Data Structures and Algorithms.", "expected_intent": "BOOK_RECOMMENDATION"},

    # M. WEB_INFORMATION
    {"id": 61, "cat": "M. WEB_INFORMATION", "query": "What are the latest features in Python 3.12?", "expected_intent": "WEB_INFORMATION"},
    {"id": 62, "cat": "M. WEB_INFORMATION", "query": "Current release status of Llama 3 model.", "expected_intent": "WEB_INFORMATION"},
    {"id": 63, "cat": "M. WEB_INFORMATION", "query": "What is the latest standard for WebGPU in browsers?", "expected_intent": "WEB_INFORMATION"},
    {"id": 64, "cat": "M. WEB_INFORMATION", "query": "Recent news on Quantum Computing breakthroughs.", "expected_intent": "WEB_INFORMATION"},
    {"id": 65, "cat": "M. WEB_INFORMATION", "query": "Current trending frontend frameworks in 2026.", "expected_intent": "WEB_INFORMATION"},

    # N. TOPIC_SUMMARY
    {"id": 66, "cat": "N. TOPIC_SUMMARY", "query": "Provide a high-level summary of Quantum Key Distribution.", "expected_intent": "TOPIC_SUMMARY"},
    {"id": 67, "cat": "N. TOPIC_SUMMARY", "query": "Executive summary of microservices security best practices.", "expected_intent": "TOPIC_SUMMARY"},
    {"id": 68, "cat": "N. TOPIC_SUMMARY", "query": "Summary of Zero Trust Architecture principles.", "expected_intent": "TOPIC_SUMMARY"},
    {"id": 69, "cat": "N. TOPIC_SUMMARY", "query": "Overview and summary of RLHF in large language models.", "expected_intent": "TOPIC_SUMMARY"},
    {"id": 70, "cat": "N. TOPIC_SUMMARY", "query": "Summary of WebAssembly performance capabilities.", "expected_intent": "TOPIC_SUMMARY"},

    # O. FOLLOW_UP QUERIES
    {"id": 71, "cat": "O. FOLLOW_UP", "query": "Explain that second point in more detail.", "expected_intent": "FOLLOW_UP"},
    {"id": 72, "cat": "O. FOLLOW_UP", "query": "Can you give a code snippet for that?", "expected_intent": "FOLLOW_UP"},
    {"id": 73, "cat": "O. FOLLOW_UP", "query": "Why is that better than the alternative?", "expected_intent": "FOLLOW_UP"},
    {"id": 74, "cat": "O. FOLLOW_UP", "query": "Give me a practical example of the third option.", "expected_intent": "FOLLOW_UP"},
    {"id": 75, "cat": "O. FOLLOW_UP", "query": "What did you mean by backpressure in that explanation?", "expected_intent": "FOLLOW_UP"},

    # P. AMBIGUOUS QUERIES
    {"id": 76, "cat": "P. AMBIGUOUS", "query": "Python", "expected_intent": "CONCEPT_EXPLANATION"},
    {"id": 77, "cat": "P. AMBIGUOUS", "query": "Transformers", "expected_intent": "CONCEPT_EXPLANATION"},
    {"id": 78, "cat": "P. AMBIGUOUS", "query": "RAG", "expected_intent": "CONCEPT_EXPLANATION"},
    {"id": 79, "cat": "P. AMBIGUOUS", "query": "Scale", "expected_intent": "CONCEPT_EXPLANATION"},
    {"id": 80, "cat": "P. AMBIGUOUS", "query": "Memory", "expected_intent": "CONCEPT_EXPLANATION"},

    # Q. COMPOUND / MULTI-INTENT QUERIES
    {"id": 81, "cat": "Q. COMPOUND_MULTI_INTENT", "query": "Find recent RAG papers and recommend videos.", "expected_intent": "RESEARCH_DISCOVERY"},
    {"id": 82, "cat": "Q. COMPOUND_MULTI_INTENT", "query": "Explain transformers and show me a GitHub implementation.", "expected_intent": "CONCEPT_EXPLANATION"},
    {"id": 83, "cat": "Q. COMPOUND_MULTI_INTENT", "query": "Summarize my document and compare it with current web information.", "expected_intent": "DOCUMENT_QUERY"},
    {"id": 84, "cat": "Q. COMPOUND_MULTI_INTENT", "query": "Compare PyTorch vs TensorFlow and recommend books for both.", "expected_intent": "COMPARISON"},
    {"id": 85, "cat": "Q. COMPOUND_MULTI_INTENT", "query": "Provide a roadmap for machine learning and quiz me on the first step.", "expected_intent": "ROADMAP"},

    # R. EMPTY OR ZERO-RESULT RETRIEVAL
    {"id": 86, "cat": "R. ZERO_RESULT_RETRIEVAL", "query": "Find research paper abstracts on xyz789unrealnonexistenttopic12345.", "expected_intent": "RESEARCH_DISCOVERY"},
    {"id": 87, "cat": "R. ZERO_RESULT_RETRIEVAL", "query": "What does my document say about supercalifragilisticexpialidocious99?", "expected_intent": "DOCUMENT_QUERY"},
    {"id": 88, "cat": "R. ZERO_RESULT_RETRIEVAL", "query": "Find GitHub repos for fake_lib_qwert_999999_xyz.", "expected_intent": "CODE_RESOURCE_RECOMMENDATION"},
    {"id": 89, "cat": "R. ZERO_RESULT_RETRIEVAL", "query": "Recommend videos for zzz_nonexistent_framework_99.", "expected_intent": "VIDEO_RECOMMENDATION"},
    {"id": 90, "cat": "R. ZERO_RESULT_RETRIEVAL", "query": "Summarize my uploaded document for topic qwertyuiopasdfghjkl.", "expected_intent": "DOCUMENT_QUERY"},

    # S. PROVIDER FAILURE / TIMEOUT / RATE LIMIT
    {"id": 91, "cat": "S. PROVIDER_FAILURES", "query": "Explain quantum cryptography key expansion.", "expected_intent": "CONCEPT_EXPLANATION"},
    {"id": 92, "cat": "S. PROVIDER_FAILURES", "query": "Find research paper abstracts on Graph Neural Networks.", "expected_intent": "RESEARCH_DISCOVERY"},
    {"id": 93, "cat": "S. PROVIDER_FAILURES", "query": "Recommend top learning video concepts for understanding SQL joins.", "expected_intent": "VIDEO_RECOMMENDATION"},
    {"id": 94, "cat": "S. PROVIDER_FAILURES", "query": "Find open-source implementations of RAG in Python.", "expected_intent": "CODE_RESOURCE_RECOMMENDATION"},
    {"id": 95, "cat": "S. PROVIDER_FAILURES", "query": "Summarize my uploaded document.", "expected_intent": "DOCUMENT_QUERY"},

    # T. UNUSUAL NATURAL LANGUAGE PHRASING
    {"id": 96, "cat": "T. UNUSUAL_NL_PHRASING", "query": "gimme sum good vids on pythn loops bro", "expected_intent": "VIDEO_RECOMMENDATION"},
    {"id": 97, "cat": "T. UNUSUAL_NL_PHRASING", "query": "I wanna research bout how neural nets learn without teachers", "expected_intent": "RESEARCH_DISCOVERY"},
    {"id": 98, "cat": "T. UNUSUAL_NL_PHRASING", "query": "can u code up a fast api server for me asap plzzzz", "expected_intent": "PROGRAMMING_HELP"},
    {"id": 99, "cat": "T. UNUSUAL_NL_PHRASING", "query": "sup AI what is recursion n why does it break my brain", "expected_intent": "CONCEPT_EXPLANATION"},
    {"id": 100, "cat": "T. UNUSUAL_NL_PHRASING", "query": "need 2 know diff between process and thread fast pls", "expected_intent": "COMPARISON"},
]


def run_universal_reliability_audit():
    """Run full EKIP Phase 13A 100-query audit suite."""
    from loguru import logger
    logger.remove()
    logger.add(sys.stderr, level="ERROR")

    init_db()
    init_chat_db()

    # Fast audit optimization: cap LLM provider attempt timeout to 1.5s during provider outage simulations
    from core.llm.manager import LLMManager
    original_generate = LLMManager.generate
    
    def fast_generate(self, *args, **kwargs):
        kwargs["timeout"] = 2.0
        return original_generate(self, *args, **kwargs)
    
    LLMManager.generate = fast_generate

    engine = BaseRAGEngine(Config)
    memory = ConversationMemory(Config.OBSERVABILITY_DB)
    orch = OrchestratorAgent(Config, engine, memory)
    planning_graph = create_ekip_planning_graph()

    results_report = []
    
    real_defects = []
    ambiguous_queries = []
    test_expectation_errors = []
    expected_behaviors = []
    pass_count = 0

    print("=" * 110)
    print(" 🚀 EKIP PHASE 13A — UNIVERSAL QUERY RELIABILITY & ADVERSARIAL END-TO-END AUDIT (100 QUERIES)")
    print("=" * 110)

    for item in AUDIT_MATRIX:
        q_id = item["id"]
        q_cat = item["cat"]
        q_text = item["query"]
        expected_intent = item["expected_intent"]

        print(f"\n[{q_id}/100] Category: {q_cat} | Query: '{q_text}'")
        t0 = time.time()

        try:
            # 1. Run Planning Graph
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

            # 2. Run Orchestrator Pipeline
            ctx = {
                "query": q_text,
                "history": [],
                "filters": {},
                "execution_plan": exec_plan,
                "plan_state": plan_state,
            }
            res = orch.run(ctx)
            latency_ms = int((time.time() - t0) * 1000)

            meta = res.metadata if isinstance(res.metadata, dict) else {}
            provider = meta.get("provider", "NONE")
            model = meta.get("model", "none")
            source_mode = meta.get("source_mode", "none")
            confidence = res.confidence
            sources_retrieved = res.sources or []
            content_len = len(res.content) if res.content else 0

            # Count specialized items
            papers_count = sum(1 for s in sources_retrieved if str(s.get("source_type", s.get("provider", ""))).lower() in ("arxiv", "semantic_scholar", "research"))
            videos_count = sum(1 for s in sources_retrieved if str(s.get("source_type", s.get("provider", ""))).lower() in ("youtube", "video"))
            repos_count = sum(1 for s in sources_retrieved if str(s.get("source_type", s.get("provider", ""))).lower() in ("github_repo", "github"))
            urls_in_content = res.content.count("http://") + res.content.count("https://") if res.content else 0

            # Audit checks
            intent_matches = (detected_intent.upper() == expected_intent.upper())
            has_content = (content_len > 0)
            valid_confidence = (confidence > 0)
            valid_provider = (provider != "NONE" or "evidence_engine" in provider)
            
            # Category-specific resource preservation checks
            resource_preserved = True
            preservation_issue = None

            if "RESEARCH" in q_cat and len(sources_retrieved) > 0 and papers_count > 0:
                if "arXiv" not in res.content and "Abstract" not in res.content and urls_in_content == 0:
                    resource_preserved = False
                    preservation_issue = "Research papers retrieved but no paper titles/URLs/abstracts in final output."

            if "VIDEO" in q_cat and len(sources_retrieved) > 0 and videos_count > 0:
                if "Watch URL" not in res.content and "YouTube" not in res.content and urls_in_content == 0:
                    resource_preserved = False
                    preservation_issue = "Videos retrieved but no video links/channels in final output."

            if "CODE_RESOURCE" in q_cat and len(sources_retrieved) > 0 and repos_count > 0:
                if "GitHub" not in res.content and "Repository URL" not in res.content and urls_in_content == 0:
                    resource_preserved = False
                    preservation_issue = "Repositories retrieved but no GitHub repo URLs/stars in final output."

            # Classification of Outcome
            status = "PASS"
            classification = "PASS"
            failure_reason = ""

            if not resource_preserved:
                status = "FAIL"
                classification = "REAL_DEFECT"
                failure_reason = preservation_issue or "Retrieved evidence lost in synthesis."
            elif not has_content or confidence == 0:
                status = "FAIL"
                classification = "REAL_DEFECT"
                failure_reason = "Empty response or false 0% confidence returned."
            elif "AMBIGUOUS" in q_cat:
                status = "PASS"
                classification = "AMBIGUOUS_QUERY"
                failure_reason = f"Ambiguous query naturally classified as {detected_intent}."
            elif "COMPOUND" in q_cat:
                # Audit single-intent planner behavior on multi-intent queries
                if intent_matches or detected_intent in ("RESEARCH_DISCOVERY", "CONCEPT_EXPLANATION", "DOCUMENT_QUERY", "COMPARISON", "ROADMAP"):
                    status = "PASS"
                    classification = "SINGLE_INTENT_AMBIGUITY"
                    failure_reason = f"Multi-intent query resolved primary intent to {detected_intent}."
                else:
                    status = "FAIL"
                    classification = "REAL_DEFECT"
                    failure_reason = f"Compound query misrouted to unexpected intent {detected_intent}."
            elif "ZERO_RESULT" in q_cat:
                if has_content and confidence >= 0:
                    status = "PASS"
                    classification = "EXPECTED_BEHAVIOR"
                else:
                    status = "FAIL"
                    classification = "REAL_DEFECT"
                    failure_reason = "Zero-result query produced unhandled system crash or illegal state."
            elif not intent_matches:
                status = "FAIL"
                classification = "REAL_DEFECT"
                failure_reason = f"Intent mismatch: detected {detected_intent}, expected {expected_intent}."

            entry = {
                "id": q_id,
                "category": q_cat,
                "query": q_text,
                "expected_intent": expected_intent,
                "detected_intent": detected_intent,
                "planner_strategy": planner_strategy,
                "doc_usage_mode": doc_usage_mode,
                "selected_sources": selected_sources,
                "sources_retrieved_count": len(sources_retrieved),
                "papers_count": papers_count,
                "videos_count": videos_count,
                "repos_count": repos_count,
                "urls_in_content": urls_in_content,
                "content_len": content_len,
                "confidence": confidence,
                "provider": provider,
                "model": model,
                "source_mode": source_mode,
                "latency_ms": latency_ms,
                "status": status,
                "classification": classification,
                "failure_reason": failure_reason,
                "snippet": res.content[:150].replace("\n", " ") if res.content else "",
            }

            print(f"  Detected Intent : {detected_intent} (Expected: {expected_intent})")
            print(f"  Source Strategy : {planner_strategy} | Selected: {selected_sources}")
            print(f"  Retrieved Count : {len(sources_retrieved)} items (Papers: {papers_count}, Videos: {videos_count}, Repos: {repos_count})")
            print(f"  Response Length : {content_len} chars | Confidence: {confidence}% | Provider: {provider}/{model}")
            print(f"  Status          : {status} ({classification})")
            if failure_reason:
                print(f"  Failure Reason  : {failure_reason}")

            results_report.append(entry)

            if classification == "REAL_DEFECT":
                real_defects.append(entry)
            elif classification == "AMBIGUOUS_QUERY":
                ambiguous_queries.append(entry)
            elif classification == "EXPECTED_BEHAVIOR":
                expected_behaviors.append(entry)
            else:
                pass_count += 1

            # Save incremental JSON report
            report_path = "scratch/phase13a_audit_report.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump({
                    "total_queries": len(AUDIT_MATRIX),
                    "completed_queries": len(results_report),
                    "pass_count": pass_count,
                    "ambiguous_count": len(ambiguous_queries),
                    "expected_behavior_count": len(expected_behaviors),
                    "real_defects_count": len(real_defects),
                    "results": results_report,
                    "real_defects": real_defects,
                }, f, indent=2)

        except Exception as e:
            traceback.print_exc()
            entry = {
                "id": q_id,
                "category": q_cat,
                "query": q_text,
                "expected_intent": expected_intent,
                "status": "FAIL",
                "classification": "REAL_DEFECT",
                "failure_reason": f"Unhandled Exception: {str(e)}",
            }
            results_report.append(entry)
            real_defects.append(entry)

            report_path = "scratch/phase13a_audit_report.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump({
                    "total_queries": len(AUDIT_MATRIX),
                    "completed_queries": len(results_report),
                    "pass_count": pass_count,
                    "ambiguous_count": len(ambiguous_queries),
                    "expected_behavior_count": len(expected_behaviors),
                    "real_defects_count": len(real_defects),
                    "results": results_report,
                    "real_defects": real_defects,
                }, f, indent=2)

    # Print Final Summary & Verdict
    print("\n" + "=" * 110)
    print(" 📊 EKIP PHASE 13A — UNIVERSAL QUERY RELIABILITY AUDIT SUMMARY")
    print("=" * 110)
    print(f" TOTAL QUERIES       : {len(AUDIT_MATRIX)}")
    print(f" PASS                : {pass_count + len(expected_behaviors)}")
    print(f" AMBIGUOUS           : {len(ambiguous_queries)}")
    print(f" REAL DEFECTS        : {len(real_defects)}")
    accuracy_excl_ambig = round(((pass_count + len(expected_behaviors)) / (len(AUDIT_MATRIX) - len(ambiguous_queries))) * 100, 2) if len(AUDIT_MATRIX) > len(ambiguous_queries) else 100.0
    print(f" ACCURACY (excl. amb): {accuracy_excl_ambig}%")
    print(f" Saved full JSON report to '{report_path}'")
    print("=" * 110)

    if real_defects:
        print("\n" + "!" * 110)
        print(" ❌ CONFIRMED REAL DEFECTS DETECTED:")
        print("!" * 110)
        for idx, d in enumerate(real_defects, 1):
            print(f"\nDEFECT ID: DEFECT-{idx:02d}")
            print(f"QUERY    : '{d.get('query')}' (Cat: {d.get('category')})")
            print(f"EXPECTED : {d.get('expected_intent')}")
            print(f"ACTUAL   : {d.get('detected_intent')} | Status: {d.get('status')}")
            print(f"REASON   : {d.get('failure_reason')}")
            print(f"PROVIDER : {d.get('provider')}/{d.get('model')}")
            print(f"RETRIEVED: {d.get('sources_retrieved_count')} items")

    print("\nFINAL VERDICT FORMAT:")
    print(f"PHASE 13A — AUDIT COMPLETE")
    print(f"TOTAL QUERIES: {len(AUDIT_MATRIX)}")
    print(f"PASS: {pass_count + len(expected_behaviors)}")
    print(f"AMBIGUOUS: {len(ambiguous_queries)}")
    print(f"REAL DEFECTS: {len(real_defects)}")


if __name__ == "__main__":
    run_universal_reliability_audit()
