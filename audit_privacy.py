import ast
import py_compile
import sys

py_compile.compile("app.py", doraise=True)

with open("app.py", "r", encoding="utf-8") as f:
    tree = ast.parse(f.read(), filename="app.py")

forbidden_names = {"open", "sqlite3", "pickle", "shelve"}
for node in ast.walk(tree):
    if isinstance(node, ast.Name) and node.id in forbidden_names:
        print(f"Privacy violation: forbidden identifier '{node.id}' found in app.py")
        sys.exit(1)
    if isinstance(node, ast.Attribute) and node.attr in {"write_text", "write_bytes"}:
        print(f"Privacy violation: forbidden file write '{node.attr}' found in app.py")
        sys.exit(1)

print("Privacy & syntax audit passed: zero disk-writing calls detected.")
