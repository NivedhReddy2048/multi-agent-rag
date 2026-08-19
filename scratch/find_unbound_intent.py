import ast
import glob
import os

def check_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except Exception as e:
            return

    class IntentVisitor(ast.NodeVisitor):
        def __init__(self):
            self.current_func = None

        def visit_FunctionDef(self, node):
            old_func = self.current_func
            self.current_func = node.name
            
            # Find all Name nodes with id == 'intent'
            assigned_in_if = []
            used_nodes = []
            
            for child in ast.walk(node):
                if isinstance(child, ast.Assign):
                    for target in child.targets:
                        if isinstance(target, ast.Name) and target.id == 'intent':
                            # Check if parent is inside an If/Try/For block
                            assigned_in_if.append(child.lineno)
                elif isinstance(child, ast.Name) and child.id == 'intent':
                    used_nodes.append((child.lineno, type(child.ctx).__name__))

            if assigned_in_if or any(u[1] == 'Load' for u in used_nodes):
                print(f"File: {filepath} | Func: {node.name}")
                print(f"  Assigned at lines: {assigned_in_if}")
                print(f"  Used (Load/Store) at: {used_nodes}")

            self.generic_visit(node)
            self.current_func = old_func

    IntentVisitor().visit(tree)

def main():
    py_files = glob.glob("**/*.py", recursive=True)
    for pf in py_files:
        if "venv" in pf or ".git" in pf or "scratch" in pf:
            continue
        check_file(pf)

if __name__ == "__main__":
    main()
