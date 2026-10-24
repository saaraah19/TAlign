"""
Architectural test: the Job module must not depend on the Workflow
Engine or Agents.

This isn't a docstring promise — it's checked mechanically. If a future
edit adds `from app.workflow_engine import ...` to job_service.py (even
transitively, e.g. via a helper that imports it), this test fails. This
is intentionally a static source check (not just "does it import at
runtime cleanly") so the rule holds even for imports inside functions
that wouldn't be hit by a normal test run.
"""

import ast
from pathlib import Path

FORBIDDEN_PREFIXES = ("app.workflow_engine", "app.agents", "app.compass")

JOB_MODULE_FILES = [
    Path(__file__).parent.parent / "app" / "services" / "job_service.py",
    Path(__file__).parent.parent / "app" / "repositories" / "job_repository.py",
    Path(__file__).parent.parent / "app" / "models" / "job.py",
    Path(__file__).parent.parent / "app" / "domain" / "events.py",
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


def test_job_module_does_not_import_workflow_engine_agents_or_compass() -> None:
    for path in JOB_MODULE_FILES:
        imported = _imported_modules(path)
        violations = {
            mod for mod in imported if any(mod.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)
        }
        assert not violations, (
            f"{path.name} imports {violations} — the Job domain must not "
            f"depend on the Workflow Engine, Agents, or Compass."
        )


def test_domain_events_module_does_not_import_workflow_engine_agents_or_compass() -> None:
    """
    The shared app/domain/events.py vocabulary must stay a leaf module —
    it can be imported BY job_service.py (and later other domains), but
    it must never import FROM workflow_engine/agents/compass itself,
    or the "one-way" dependency direction described in its own
    docstring would be false.
    """
    path = Path(__file__).parent.parent / "app" / "domain" / "events.py"
    imported = _imported_modules(path)
    violations = {
        mod for mod in imported if any(mod.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)
    }
    assert not violations
