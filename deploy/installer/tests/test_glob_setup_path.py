import ast
import pathlib


repository = pathlib.Path(__file__).parents[3]
source = (repository / "gui" / "fragments" / "glob.py").read_text(encoding="utf-8")
tree = ast.parse(source)

calls = [
    node for node in ast.walk(tree)
    if isinstance(node, ast.Call)
    and isinstance(node.func, ast.Name)
    and node.func.id == "resolve_setup_toml"
]

assert calls, "glob.py must resolve setup.toml through the shared resolver"
assert any(call.args for call in calls), (
    "glob.py must pass its code-derived BAAS root instead of relying on the process working directory"
)
