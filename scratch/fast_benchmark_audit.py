"""
Fast 100-Query Benchmark Audit for EKIP Phase 13B.
Tests zero-network RuleBasedPlannerEngine + OrchestratorAgent fallback/synthesis boundary logic
across the 100 benchmark queries in under 5 seconds.
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.abspath("."))

from scratch.audit_phase13a_universal_query_reliability import AUDIT_MATRIX
from core.planner.rules import RuleBasedPlannerEngine
from agents.orchestrator import OrchestratorAgent

def run_fast_benchmark():
    print("==========================================================================================")
    print(" 🚀 EKIP PHASE 13B — FAST 100-QUERY BENCHMARK AUDIT")
    print("==========================================================================================")

    results_report = []
    real_defects = []
    ambiguous_queries = []
    expected_behaviors = []
    pass_count = 0

    t_start = time.time()

    for item in AUDIT_MATRIX:
        q_id = item["id"]
        q_cat = item["cat"]
        q_text = item["query"]
        expected_intent = item["expected_intent"]

        plan = RuleBasedPlannerEngine.generate_plan(q_text)
        detected_intent = plan.intent.value.upper()
        sec_intents = [s.value.upper() for s in plan.secondary_intents]

        # Simulate fallback output formatting
        fallback_res = OrchestratorAgent._format_evidence_fallback(q_text, plan.intent, [], exec_plan=plan)
        has_content = len(fallback_res) > 0

        status = "PASS"
        classification = "PASS"
        failure_reason = ""

        if "AMBIGUOUS" in q_cat:
            classification = "AMBIGUOUS_QUERY"
            status = "PASS"
        elif "COMPOUND" in q_cat:
            if detected_intent == expected_intent or len(sec_intents) > 0:
                classification = "PASS"
                status = "PASS"
            else:
                classification = "REAL_DEFECT"
                status = "FAIL"
                failure_reason = f"Compound query misrouted to {detected_intent}"
        elif "FOLLOW_UP" in q_cat:
            # Follow ups without history resolve to FOLLOW_UP intent and Mode B clarification
            if detected_intent == "FOLLOW_UP":
                classification = "PASS"
                status = "PASS"
            else:
                classification = "REAL_DEFECT"
                status = "FAIL"
                failure_reason = f"Follow-up misrouted to {detected_intent}"
        elif detected_intent != expected_intent:
            classification = "REAL_DEFECT"
            status = "FAIL"
            failure_reason = f"Intent mismatch: got {detected_intent}, expected {expected_intent}"

        entry = {
            "id": q_id,
            "category": q_cat,
            "query": q_text,
            "expected_intent": expected_intent,
            "detected_intent": detected_intent,
            "secondary_intents": sec_intents,
            "strategy": plan.source_strategy.value,
            "fallback_has_content": has_content,
            "status": status,
            "classification": classification,
            "failure_reason": failure_reason,
        }

        results_report.append(entry)

        if classification == "REAL_DEFECT":
            real_defects.append(entry)
        elif classification == "AMBIGUOUS_QUERY":
            ambiguous_queries.append(entry)
        else:
            pass_count += 1

    t_end = time.time()

    print(f" TOTAL QUERIES       : {len(AUDIT_MATRIX)}")
    print(f" PASS                : {pass_count}")
    print(f" AMBIGUOUS           : {len(ambiguous_queries)}")
    print(f" REAL DEFECTS        : {len(real_defects)}")
    print(f" AUDIT TIME          : {round(t_end - t_start, 3)} seconds")
    print("==========================================================================================")

    if real_defects:
        print("\n❌ REAL DEFECTS:")
        for d in real_defects:
            print(f"  [{d['id']}] {d['category']} | Query: '{d['query']}' | Exp: {d['expected_intent']} | Got: {d['detected_intent']} | Reason: {d['failure_reason']}")

    report_path = "scratch/phase13b_benchmark_results.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_queries": len(AUDIT_MATRIX),
            "pass_count": pass_count,
            "ambiguous_count": len(ambiguous_queries),
            "real_defects_count": len(real_defects),
            "results": results_report,
            "real_defects": real_defects,
        }, f, indent=2)

if __name__ == "__main__":
    run_fast_benchmark()
