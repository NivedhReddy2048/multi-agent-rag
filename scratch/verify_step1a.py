import sys
import os
import traceback

sys.path.insert(0, os.path.abspath("."))

with open("scratch/step1a_out.txt", "w", encoding="utf-8") as f:
    f.write("=== STEP 1-A VERIFICATION ===\n")
    try:
        from core.planner.rules import RuleBasedPlannerEngine
        queries = [
            "gimme sum good vids on pythn loops bro",
            "can u code up a fast api server for me asap plzzzz",
            "need 2 know diff between process and thread fast pls",
            "Find recent preprints on Graph Neural Networks.",
            "Write a Dockerfile for a FastAPI application."
        ]
        for q in queries:
            norm = RuleBasedPlannerEngine.normalize_query(q)
            plan = RuleBasedPlannerEngine.generate_plan(q)
            f.write(f"ORIGINAL:   {q}\n")
            f.write(f"NORMALIZED: {norm}\n")
            f.write(f"INTENT:     {plan.intent.value}\n")
            f.write("-" * 50 + "\n")
    except Exception as e:
        f.write("ERROR:\n" + traceback.format_exc())
