"""
Architectural test: the Application module must not depend on the
Workflow Engine, Agents, or Compass — same rule and same mechanism as
tests/test_job_workflow_independence.py, applied to the Application
module's files.

The flow specified for Slice 3 is exactly:

    User action -> ApplicationService -> validate -> persist -> return

with no Workflow Engine step anywhere in it. This test makes that a
mechanically-checked fact, not just a docstring claim.
"""

import ast
from pathlib import Path

FORBIDDEN_PREFIXES = ("app.workflow_engine", "app.agents", "app.compass")

APPLICATION_MODULE_FILES = [
    Path(__file__).parent.parent / "app" / "services" / "application_service.py",
    Path(__file__).parent.parent / "app" / "repositories" / "application_repository.py",
    Path(__file__).parent.parent / "app" / "models" / "application.py",
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


def test_application_module_does_not_import_workflow_engine_agents_or_compass() -> None:
    for path in APPLICATION_MODULE_FILES:
        imported = _imported_modules(path)
        violations = {
            mod
            for mod in imported
            if any(mod.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)
        }
        assert not violations, (
            f"{path.name} imports {violations} — the Application domain must "
            f"not depend on the Workflow Engine, Agents, or Compass."
        )
