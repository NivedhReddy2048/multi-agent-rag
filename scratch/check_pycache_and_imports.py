"""
Script to inspect sys.path, all pycache directories, and trace exact imports used by app.py.
"""

import sys
import os
import glob
import inspect

sys.path.insert(0, os.path.abspath("."))

def find_pycache():
    pyc_files = glob.glob("**/*.pyc", recursive=True)
    print(f"Found {len(pyc_files)} .pyc files in project.")
    for f in pyc_files:
        print(f"  - {f}")

def check_app_imports():
    import app
    import agents.orchestrator
    import core.planner.rules
    import graph.nodes.planning_nodes
    import graph.builder

    print("\n--- APP IMPORT LOCATIONS ---")
    print(f"app                          : {getattr(app, '__file__', 'N/A')}")
    print(f"agents.orchestrator          : {getattr(agents.orchestrator, '__file__', 'N/A')}")
    print(f"core.planner.rules           : {getattr(core.planner.rules, '__file__', 'N/A')}")
    print(f"graph.nodes.planning_nodes   : {getattr(graph.nodes.planning_nodes, '__file__', 'N/A')}")
    print(f"graph.builder                : {getattr(graph.builder, '__file__', 'N/A')}")

    print("\n--- SOURCE FILES ---")
    from agents.orchestrator import OrchestratorAgent
    print(f"OrchestratorAgent file       : {inspect.getfile(OrchestratorAgent)}")
    print(f"OrchestratorAgent.run source : {inspect.getsourcefile(OrchestratorAgent.run)}")
    print(f"OrchestratorAgent.dispatch   : {inspect.getsourcefile(OrchestratorAgent.dispatch_selected_sources)}")

if __name__ == "__main__":
    find_pycache()
    check_app_imports()
