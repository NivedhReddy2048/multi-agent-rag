import sys
import inspect
import importlib
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

test_modules = [
    "tests.test_prompt_builder_quality",
    "tests.test_planner_target_matching",
    "tests.test_llm_provider_reliability",
    "tests.test_step2c_relevance_gating",
]

passed_count = 0
failed_count = 0

for mod_name in test_modules:
    print(f"\n==========================================", flush=True)
    print(f"MODULE: {mod_name}", flush=True)
    print(f"==========================================", flush=True)
    try:
        mod = importlib.import_module(mod_name)
    except Exception as e:
        print(f"FAILED TO IMPORT {mod_name}: {e}", flush=True)
        traceback.print_exc()
        failed_count += 1
        continue

    funcs = [obj for name, obj in inspect.getmembers(mod, inspect.isfunction) if name.startswith("test_")]
    classes = [obj for name, obj in inspect.getmembers(mod, inspect.isclass) if name.startswith("Test") or name.endswith("Test")]

    for func in funcs:
        print(f"Running function {func.__name__}...", end="", flush=True)
        try:
            func()
            print(" [PASS]", flush=True)
            passed_count += 1
        except Exception as e:
            print(f" [FAIL: {type(e).__name__}: {e}]", flush=True)
            traceback.print_exc()
            failed_count += 1

    for cls in classes:
        print(f"Running TestCase class {cls.__name__}...", flush=True)
        methods = [m for m in dir(cls) if m.startswith("test_")]
        methods.sort()
        for m_name in methods:
            print(f"  - Method {m_name}...", end="", flush=True)
            try:
                inst = cls()
                if hasattr(inst, "setUp"):
                    inst.setUp()
                getattr(inst, m_name)()
                print(" [PASS]", flush=True)
                passed_count += 1
            except Exception as e:
                print(f" [FAIL: {type(e).__name__}: {e}]", flush=True)
                traceback.print_exc()
                failed_count += 1

print(f"\n==========================================")
print(f"ALL REGRESSION TESTS COMPLETED")
print(f"TOTAL PASSED: {passed_count}")
print(f"TOTAL FAILED: {failed_count}")
print(f"==========================================", flush=True)

if failed_count > 0:
    sys.exit(1)
