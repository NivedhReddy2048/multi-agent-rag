"""
EKIP Phase 11G — Explicit available_docs test.
"""

import sys
import os
import traceback

sys.path.insert(0, os.path.abspath("."))

from core.planner.rules import RuleBasedPlannerEngine


def main():
    print("Testing generate_plan with available_docs=[]...", flush=True)
    query = "Explain the core concepts of Transformer architectures in Machine Learning."

    try:
        plan = RuleBasedPlannerEngine.generate_plan(query, [], available_docs=[])
        print(f"Plan generated successfully! Intent: {plan.intent}, Strategy: {plan.source_strategy}", flush=True)
    except BaseException as e:
        print(f"generate_plan FAILED with BaseException [{type(e).__name__}]: {e}", flush=True)
        traceback.print_exc()


if __name__ == "__main__":
    main()
