"""
Architectural test: Resume Intelligence must not depend on the Workflow
Engine, matching the same doctrine already enforced for Job (Slice 2)
and Application (Slice 3). Not explicitly required for Slice 4, but kept
consistent with the established pattern — the Resume Intelligence Agent
must never trigger pipeline transitions or business workflows itself
(per explicit instruction: "it should never move applications through
the pipeline, change application status, or trigger hiring workflows").
"""

import ast
from pathlib import Path

FORBIDDEN_PREFIXES = ("app.workflow_engine",)

RESUME_INTELLIGENCE_FILES = [
    Path(__file__).parent.parent / "app" / "agents" / "resume_intelligence" / "agent.py",
    Path(__file__).parent.parent / "app" / "agents" / "resume_intelligence" / "scoring.py",
    Path(__file__).parent.parent / "app" / "agents" / "resume_intelligence" / "prompts.py",
    Path(__file__).parent.parent / "app" / "agents" / "resume_intelligence" / "schemas.py",
    Path(__file__).parent.parent / "app" / "services" / "resume_service.py",
    Path(__file__).parent.parent / "app" / "services" / "resume_analysis_service.py",
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


def test_resume_intelligence_does_not_import_workflow_engine() -> None:
    for path in RESUME_INTELLIGENCE_FILES:
        imported = _imported_modules(path)
        violations = {
            mod for mod in imported if any(mod.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)
        }
        assert not violations, (
            f"{path.name} imports {violations} — the Resume Intelligence Agent "
            f"must never trigger workflows or pipeline transitions itself."
        )
