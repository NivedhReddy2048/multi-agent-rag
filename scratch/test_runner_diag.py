import os
import sys
import traceback

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

sys.stdout.write("Starting test_runner_diag.py...\n")
sys.stdout.flush()

try:
    sys.stdout.write("Importing Config...\n")
    sys.stdout.flush()
    from config.settings import Config
    cfg = Config()

    sys.stdout.write("Importing BaseRAGEngine...\n")
    sys.stdout.flush()
    from core.engine import BaseRAGEngine

    sys.stdout.write("Importing OrchestratorAgent...\n")
    sys.stdout.flush()
    from agents.orchestrator import OrchestratorAgent

    sys.stdout.write("All imports successful!\n")
    sys.stdout.flush()
except Exception as e:
    sys.stdout.write(f"ERROR: {e}\n")
    traceback.print_exc(file=sys.stdout)
    sys.stdout.flush()
