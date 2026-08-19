import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_step2c_relevance_gating import TestStep2CRelevanceGating

test_inst = TestStep2CRelevanceGating()

test_methods = [m for m in dir(test_inst) if m.startswith("test_")]
test_methods.sort()

passed = 0
failed = 0

print(f"Executing {len(test_methods)} tests...\n", flush=True)

for method_name in test_methods:
    print(f"Running {method_name}...", end="", flush=True)
    try:
        test_inst.setUp()
        method = getattr(test_inst, method_name)
        method()
        print(" [PASS]", flush=True)
        passed += 1
    except Exception as e:
        print(f" [FAIL: {type(e).__name__}: {e}]", flush=True)
        traceback.print_exc()
        failed += 1

print(f"\nSummary: {passed} PASSED, {failed} FAILED", flush=True)
