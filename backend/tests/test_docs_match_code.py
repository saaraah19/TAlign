"""
Documentation that is generated from, or checked against, the code.

Three documents contain facts that would go stale the moment someone edits the
code, so each embeds a block produced by a script, and these tests fail if the
embedded block no longer matches what the script produces now:

  * docs/04_permissions.md  — endpoint access table   (scripts/route_access.py)
  * docs/06_data_model.md   — data dictionary         (scripts/schema_doc.py)
  * the endpoint list itself must equal what FastAPI publishes in OpenAPI, so
    the access extractor cannot silently miss a route.

If one of these fails, the code changed and the document did not. Regenerate:
    python scripts/route_access.py --markdown
    python scripts/schema_doc.py
and paste the output between the BEGIN/END markers in the document.

The docs/ folder lives at the repository root, outside backend/. In the
backend Docker container only backend/ is mounted, so the document checks are
skipped there; they run in CI and in a normal checkout.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
DOCS = BACKEND.parent / "docs"


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, BACKEND / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module  # @dataclass looks its own module up here
    spec.loader.exec_module(module)
    return module


def _embedded_block(document: Path, begin: str, end: str) -> str:
    text = document.read_text(encoding="utf-8").replace("\r\n", "\n")
    match = re.search(re.escape(begin) + r".*?" + re.escape(end), text, flags=re.DOTALL)
    assert match, f"{document.name} has no block between {begin!r} and {end!r}"
    return match.group(0)


def test_route_access_extractor_covers_exactly_the_openapi_operations() -> None:
    """The extractor reads source code; OpenAPI reads the live app. They must agree."""
    from app.main import create_app

    route_access = _load_script("route_access")
    published = {
        (method.upper(), path)
        for path, item in create_app().openapi()["paths"].items()
        for method in item
    }
    extracted = {(r.method, r.path) for r in route_access.collect_route_access()}
    assert extracted == published, (
        f"only in OpenAPI: {sorted(published - extracted)}; "
        f"only extracted: {sorted(extracted - published)}"
    )


@pytest.mark.skipif(not DOCS.exists(), reason="docs/ is not mounted (backend-only container)")
def test_permissions_doc_access_table_matches_code() -> None:
    route_access = _load_script("route_access")
    embedded = _embedded_block(
        DOCS / "04_permissions.md",
        route_access.ACCESS_TABLE_BEGIN,
        route_access.ACCESS_TABLE_END,
    )
    assert embedded == route_access.render_access_table(), (
        "docs/04_permissions.md is out of date: run "
        "`python scripts/route_access.py --markdown` and replace the table."
    )


@pytest.mark.skipif(not DOCS.exists(), reason="docs/ is not mounted (backend-only container)")
def test_data_model_doc_dictionary_matches_models() -> None:
    schema_doc = _load_script("schema_doc")
    embedded = _embedded_block(
        DOCS / "06_data_model.md", schema_doc.SCHEMA_BEGIN, schema_doc.SCHEMA_END
    )
    assert embedded == schema_doc.render_data_dictionary(), (
        "docs/06_data_model.md is out of date: run `python scripts/schema_doc.py` "
        "and replace the data dictionary."
    )


@pytest.mark.skipif(not DOCS.exists(), reason="docs/ is not mounted (backend-only container)")
def test_data_model_doc_mentions_every_migrated_index() -> None:
    """Indexes live only in migrations, so check the document names each one."""
    document = (DOCS / "06_data_model.md").read_text(encoding="utf-8")
    declared = set()
    for migration in (BACKEND / "alembic" / "versions").glob("*.py"):
        declared.update(re.findall(r"create_index\(\s*[\"'](ix_[a-z0-9_]+)[\"']", migration.read_text()))
    assert declared, "no create_index calls found; the pattern needs updating"
    missing = sorted(name for name in declared if name not in document)
    assert not missing, f"indexes missing from docs/06_data_model.md: {missing}"


# --------------------------------------------------------------------------- API reference


def test_every_endpoint_has_a_reference_note() -> None:
    """A new route cannot ship without a sentence describing it in the API reference."""
    from app.main import create_app

    generator = _load_script("generate_api_reference")
    published = {
        f"{method.upper()} {path}"
        for path, item in create_app().openapi()["paths"].items()
        for method in item
    }
    assert not published - set(generator.ENDPOINT_NOTES), (
        "endpoints without a note in scripts/generate_api_reference.py ENDPOINT_NOTES: "
        f"{sorted(published - set(generator.ENDPOINT_NOTES))}"
    )
    assert not set(generator.ENDPOINT_NOTES) - published, (
        "notes for endpoints that no longer exist: "
        f"{sorted(set(generator.ENDPOINT_NOTES) - published)}"
    )


@pytest.mark.skipif(not DOCS.exists(), reason="docs/ is not mounted (backend-only container)")
def test_api_reference_structure_matches_openapi() -> None:
    """
    Compares STRUCTURE, not text: the same endpoints, the same schemas and the same field
    names per schema. A FastAPI/Pydantic upgrade that only rewords output cannot break this;
    adding, removing or renaming an endpoint or field can, which is the point.
    """
    from app.main import create_app

    spec = create_app().openapi()
    text = (DOCS / "05_api_reference.md").read_text(encoding="utf-8").replace("\r\n", "\n")

    documented_ops = set(re.findall(r"^### `([A-Z]+ /[^`]*)`", text, flags=re.MULTILINE))
    published_ops = {
        f"{method.upper()} {path}" for path, item in spec["paths"].items() for method in item
    }
    assert documented_ops == published_ops, (
        f"only documented: {sorted(documented_ops - published_ops)}; "
        f"only in the API: {sorted(published_ops - documented_ops)}. "
        "Run: python scripts/generate_api_reference.py"
    )

    skipped = {"HTTPValidationError", "ValidationError"}
    schemas = {k: v for k, v in spec["components"]["schemas"].items() if k not in skipped}
    sections = dict(
        re.findall(r"^#### `([^`]+)`\n(.*?)(?=^#### |\Z)", text, flags=re.MULTILINE | re.DOTALL)
    )
    assert set(sections) == set(schemas), (
        f"only documented: {sorted(set(sections) - set(schemas))}; "
        f"only in the API: {sorted(set(schemas) - set(sections))}. "
        "Run: python scripts/generate_api_reference.py"
    )
    for name, schema in schemas.items():
        documented_fields = set(re.findall(r"^\| `([^`]+)` \|", sections[name], flags=re.MULTILINE))
        expected_fields = set(schema.get("properties", {}))
        assert documented_fields == expected_fields, (
            f"schema {name}: documented fields {sorted(documented_fields)} "
            f"differ from the API's {sorted(expected_fields)}. "
            "Run: python scripts/generate_api_reference.py"
        )


# --------------------------------------------------------------------------- settings


@pytest.mark.skipif(not DOCS.exists(), reason="docs/ is not mounted (backend-only container)")
def test_deployment_doc_mentions_every_setting() -> None:
    """Every configuration setting must be explained in docs/09_deployment.md."""
    from app.core.config import Settings

    document = (DOCS / "09_deployment.md").read_text(encoding="utf-8")
    missing = sorted(
        name.upper() for name in Settings.model_fields if f"`{name.upper()}`" not in document
    )
    assert not missing, f"settings not documented in docs/09_deployment.md: {missing}"
