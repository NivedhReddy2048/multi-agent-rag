import sys, os, traceback
sys.path.insert(0, ".")
from core.planner.rules import RuleBasedPlannerEngine


try:
    print("Testing generate_plan...")
    plan = RuleBasedPlannerEngine.generate_plan('Explain concept.', [])
    print("SUCCESS:", plan)
except Exception as e:
    print("EXCEPTION CAUGHT:", type(e), e)
    traceback.print_exc()
