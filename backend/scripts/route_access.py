"""
Who may call which endpoint — read from the source code, not typed by hand.

Why this exists: the access rule of every route is declared in exactly one
place, as a FastAPI dependency in the route's signature
(`Depends(require_roles(Role.ADMIN, ...))`, `Depends(get_current_user)`, or
nothing at all for public routes). OpenAPI cannot express that, so the
generated API reference would otherwise have no "who may call this" column,
and the permissions document would have to be maintained by hand.

This module reads the `app/api/v1/*.py` files as syntax trees (it does not
import or run them), resolves the role constants such as `_WRITE_ROLES`, and
joins each route with the URL prefix it is mounted under in `router.py`.
Reading the syntax tree rather than introspecting the live FastAPI app is
deliberate: FastAPI changed how it exposes included routers between
versions, while the source code's shape is under our control.

Used by:
  - docs/04_permissions.md (its endpoint table is checked against this)
  - the API reference generator
  - tests/test_docs_match_code.py, which fails when a doc and the code drift.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

API_DIR = Path(__file__).resolve().parent.parent / "app" / "api" / "v1"
API_PREFIX = "/api/v1"
HTTP_VERBS = {"get", "post", "put", "patch", "delete"}

#: Access kinds that are not a list of roles.
ANY_AUTHENTICATED = "any signed-in user"
PUBLIC = "public"


@dataclass(frozen=True)
class RouteAccess:
    method: str  # "GET", "POST", ...
    path: str  # full path, e.g. "/api/v1/jobs/{job_id}"
    function: str  # handler name, e.g. "get_job"
    module: str  # file stem, e.g. "jobs"
    #: Tuple of role names (e.g. ("admin", "recruiter")), or the sentinel
    #: strings ANY_AUTHENTICATED / PUBLIC.
    access: tuple[str, ...] | str


def _role_name(node: ast.AST) -> str:
    """`Role.ADMIN` -> "admin" (the enum value, resolved from app.core.roles)."""
    from app.core.roles import Role

    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "Role"
    ):
        return Role[node.attr].value
    raise ValueError(f"Unsupported role expression: {ast.dump(node)}")


def _module_role_constants(tree: ast.Module) -> dict[str, tuple[str, ...]]:
    """Module-level `_X_ROLES = (Role.A, Role.B)` assignments."""
    constants: dict[str, tuple[str, ...]] = {}
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Tuple)
        ):
            try:
                constants[node.targets[0].id] = tuple(_role_name(e) for e in node.value.elts)
            except ValueError:
                continue  # some other tuple; not a role list
    return constants


def _access_of(
    func: ast.AsyncFunctionDef | ast.FunctionDef, constants: dict[str, tuple[str, ...]]
) -> tuple[str, ...] | str:
    defaults = list(func.args.defaults) + [d for d in func.args.kw_defaults if d is not None]
    for default in defaults:
        if not (
            isinstance(default, ast.Call)
            and isinstance(default.func, ast.Name)
            and default.func.id == "Depends"
            and default.args
        ):
            continue
        inner = default.args[0]
        if isinstance(inner, ast.Name) and inner.id == "get_current_user":
            return ANY_AUTHENTICATED
        if (
            isinstance(inner, ast.Call)
            and isinstance(inner.func, ast.Name)
            and inner.func.id == "require_roles"
        ):
            roles: list[str] = []
            for arg in inner.args:
                if isinstance(arg, ast.Starred) and isinstance(arg.value, ast.Name):
                    roles.extend(constants[arg.value.id])
                else:
                    roles.append(_role_name(arg))
            return tuple(roles)
    return PUBLIC


def _mounts() -> list[tuple[str, str]]:
    """(module stem, URL prefix) pairs, read from router.py's include_router calls."""
    tree = ast.parse((API_DIR / "router.py").read_text(encoding="utf-8"))
    imports: dict[str, str] = {}  # alias -> module stem
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith(
            "app.api.v1."
        ):
            stem = node.module.rsplit(".", 1)[1]
            for alias in node.names:
                imports[alias.asname or alias.name] = stem

    mounts: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "include_router"
            and node.args
            and isinstance(node.args[0], ast.Name)
        ):
            prefix = ""
            for kw in node.keywords:
                if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                    prefix = kw.value.value
            mounts.append((imports[node.args[0].id], prefix))
    return mounts


def collect_route_access() -> list[RouteAccess]:
    """Every endpoint with its access rule, in source order per module."""
    routes: list[RouteAccess] = []
    for stem, prefix in _mounts():
        tree = ast.parse((API_DIR / f"{stem}.py").read_text(encoding="utf-8"))
        constants = _module_role_constants(tree)
        for node in tree.body:
            if not isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
                continue
            for deco in node.decorator_list:
                if (
                    isinstance(deco, ast.Call)
                    and isinstance(deco.func, ast.Attribute)
                    and deco.func.attr in HTTP_VERBS
                    and deco.args
                    and isinstance(deco.args[0], ast.Constant)
                ):
                    routes.append(
                        RouteAccess(
                            method=deco.func.attr.upper(),
                            path=f"{API_PREFIX}{prefix}{deco.args[0].value}",
                            function=node.name,
                            module=stem,
                            access=_access_of(node, constants),
                        )
                    )
    return routes




ACCESS_TABLE_BEGIN = "<!-- BEGIN GENERATED: endpoint-access-table -->"
ACCESS_TABLE_END = "<!-- END GENERATED: endpoint-access-table -->"


def render_access_table() -> str:
    """
    The endpoint-by-endpoint access table, as Markdown, wrapped in marker
    comments so a document can embed it and a test can check it is current.
    Regenerate with:  python scripts/route_access.py --markdown
    """
    lines = [
        ACCESS_TABLE_BEGIN,
        "| Method | Path | Who may call it |",
        "| --- | --- | --- |",
    ]
    for r in collect_route_access():
        who = (
            ", ".join(f"`{role}`" for role in r.access)
            if isinstance(r.access, tuple)
            else r.access
        )
        lines.append(f"| {r.method} | `{r.path}` | {who} |")
    lines.append(ACCESS_TABLE_END)
    return "\n".join(lines)


if __name__ == "__main__":
    # python scripts/route_access.py             -> plain listing
    # python scripts/route_access.py --markdown  -> the Markdown table
    import sys

    if "--markdown" in sys.argv:
        print(render_access_table())
    else:
        for r in collect_route_access():
            print(f"{r.method:6} {r.path:58} {r.access}")
