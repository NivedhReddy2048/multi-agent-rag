import sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_step2b_synthesis_integration import (
    test_1_general_educational_query_uses_educational_prompt_builder_and_configured_timeout,
    test_2_general_educational_query_no_evidence_permits_core_knowledge,
    test_3_strict_document_query_preserves_strict_mode,
    test_4_configured_timeout_propagation,
    test_5_agent_result_backward_compatibility,
)

funcs = [
    test_1_general_educational_query_uses_educational_prompt_builder_and_configured_timeout,
    test_2_general_educational_query_no_evidence_permits_core_knowledge,
    test_3_strict_document_query_preserves_strict_mode,
    test_4_configured_timeout_propagation,
    test_5_agent_result_backward_compatibility,
]

for fn in funcs:
    print(f"Running {fn.__name__}...", flush=True)
    try:
        fn()
        print(f"PASS: {fn.__name__}", flush=True)
    except BaseException as e:
        print(f"FAIL: {fn.__name__} -> {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
        sys.stdout.flush()
