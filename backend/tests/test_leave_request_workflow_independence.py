"""
Architectural test: the Leave Request module must not depend on the
Workflow Engine, Agents, or Compass — same rule and same mechanism as
tests/test_application_workflow_independence.py, applied to Sub-slice
9c's files. Leave Management is plain deterministic persistence with no
AI or workflow-orchestration involvement at all.
"""

import ast
from pathlib import Path

FORBIDDEN_PREFIXES = ("app.workflow_engine", "app.agents", "app.compass")

LEAVE_REQUEST_MODULE_FILES = [
    Path(__file__).parent.parent / "app" / "services" / "leave_request_service.py",
    Path(__file__).parent.parent / "app" / "repositories" / "leave_request_repository.py",
    Path(__file__).parent.parent / "app" / "models" / "leave_request.py",
]


def _imported_modules(source_path: Path) -> set[str]:
    tree = ast.parse(source_path.read_text())
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_leave_request_module_does_not_import_workflow_engine_agents_or_compass() -> None:
    for path in LEAVE_REQUEST_MODULE_FILES:
        imported = _imported_modules(path)
        violations = {
            mod
            for mod in imported
            if any(mod.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)
        }
        assert not violations, (
            f"{path.name} imports {violations} — the Leave Request domain must "
            f"not depend on the Workflow Engine, Agents, or Compass."
        )
