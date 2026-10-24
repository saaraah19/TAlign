"""
Architectural test: the Workflow Engine must not depend on Compass and
must never import an LLM provider or LangChain directly.

Mirrors the AST-based approach already used by
test_job_workflow_independence.py / test_application_workflow_independence.py
/ test_resume_intelligence_workflow_independence.py, applied in the
other direction: those tests prove Job/Application/Resume Intelligence
don't depend on the Workflow Engine. This one proves the Workflow
Engine doesn't depend on Compass, and separately proves it never
touches an LLM provider directly — "invokes agents but never reasons
itself" (per the Slice 7 scope description) means every LLM call must
happen inside a Service/Agent the Workflow Engine calls into, never
inside the engine or a Workflow subclass itself.

Note: HireCandidateWorkflow legitimately imports CommunicationService
and EmployeeService — that's expected and correct (a Workflow invokes
Services). What it must never do is import app.compass or anything
LLM-related directly; those are the module boundaries checked here.
"""

import ast
from pathlib import Path

FORBIDDEN_PREFIXES = (
    "app.compass",
    "app.core.llm_provider",
    "langchain",
    "langchain_google_genai",
    "google.generativeai",
)

WORKFLOW_ENGINE_MODULE_FILES = [
    Path(__file__).parent.parent / "app" / "workflow_engine" / "engine.py",
    Path(__file__).parent.parent / "app" / "workflow_engine" / "workflow.py",
    Path(__file__).parent.parent / "app" / "workflow_engine" / "context.py",
    Path(__file__).parent.parent / "app" / "workflow_engine" / "tasks.py",
    Path(__file__).parent.parent / "app" / "workflow_engine" / "workflows" / "hire_candidate.py",
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


def test_workflow_engine_does_not_import_compass_or_an_llm_provider() -> None:
    for path in WORKFLOW_ENGINE_MODULE_FILES:
        imported = _imported_modules(path)
        violations = {
            mod
            for mod in imported
            if any(mod.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)
        }
        assert not violations, (
            f"{path.name} imports {violations} — the Workflow Engine must not "
            f"depend on Compass or call an LLM provider directly. LLM reasoning "
            f"belongs entirely inside the Services/Agents a Workflow step calls."
        )


def test_engine_module_specifically_has_no_agent_registry_dependency() -> None:
    """
    Slice 7's design fork, made mechanical: the original Slice-0 scaffold
    dispatched AI-backed steps via `agent_registry` — that assumption was
    revised (see workflow.py's module docstring) because
    CommunicationAgent/KnowledgeAgent aren't registered there. This test
    makes the reversal permanent: engine.py must never re-import
    app.agents.registry.
    """
    path = Path(__file__).parent.parent / "app" / "workflow_engine" / "engine.py"
    imported = _imported_modules(path)
    assert "app.agents.registry" not in imported
    assert "app.agents.base" not in imported
