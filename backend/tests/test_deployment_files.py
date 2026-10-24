"""
The deployment files are configuration, so mistakes in them only show up on a real deploy, the
slowest and least forgiving place to find them. These checks catch the mistakes that can be
caught without a host: rules that drifted apart, a secret typed into a file that is committed,
a misspelled environment variable, a start command that forgets the migrations.

They read render.yaml and the Dockerfiles at the repository root, which is outside backend/, so
they skip themselves in the backend-only Docker container and run in CI and in a normal checkout.
"""

import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
RENDER = ROOT / "render.yaml"
RULES = ROOT / "frontend" / "static-host-rules.json"
DOCKERFILE_PROD = ROOT / "backend" / "Dockerfile.prod"

pytestmark = pytest.mark.skipif(not RENDER.exists(), reason="repository root is not mounted")

# Variables render.yaml may set that are not fields of the backend's Settings class: they belong
# to the platform, to the build, or to Uvicorn.
NOT_BACKEND_SETTINGS = {"NODE_VERSION", "NEXT_PUBLIC_API_URL", "FORWARDED_ALLOW_IPS"}
# Names that must be prompted for (sync: false), never written into the committed file.
SECRET_NAMES = ("KEY", "SECRET", "PASSWORD", "TOKEN", "DATABASE_URL")


def _services() -> dict[str, dict]:
    return {s["name"]: s for s in yaml.safe_load(RENDER.read_text(encoding="utf-8"))["services"]}


def test_the_blueprint_describes_a_static_site_and_a_web_service_on_the_free_plan() -> None:
    services = _services()
    api, site = services["talign-api"], services["talign"]
    assert (api["type"], api["runtime"], api["plan"]) == ("web", "docker", "free")
    assert (site["type"], site["runtime"]) == ("web", "static")
    assert api["dockerfilePath"] == "./backend/Dockerfile.prod"
    assert (ROOT / "backend" / "Dockerfile.prod").exists()
    assert api["healthCheckPath"] == "/api/v1/health"


def test_page_rewrites_in_the_blueprint_equal_the_shared_rules_in_the_same_order() -> None:
    """frontend/static-host-rules.json drives the local server; render.yaml drives production."""
    shared = json.loads(RULES.read_text(encoding="utf-8"))["rewrites"]
    routes = _services()["talign"]["routes"]

    assert routes[0]["source"] == "/api/*", "the API forward must come first"
    assert routes[0]["destination"].startswith("https://") and routes[0]["destination"].endswith("/api/*")
    pages = [{"source": r["source"], "destination": r["destination"]} for r in routes[1:]]
    assert pages == shared
    assert {r["type"] for r in routes} == {"rewrite"}


def test_secrets_are_prompted_for_and_never_written_into_the_file() -> None:
    api_vars = _services()["talign-api"]["envVars"]
    by_key = {v["key"]: v for v in api_vars}

    for key, var in by_key.items():
        if any(word in key for word in SECRET_NAMES):
            assert "value" not in var, f"{key} must not carry a literal value in a committed file"
    assert by_key["GOOGLE_API_KEY"].get("sync") is False
    assert by_key["DATABASE_URL"].get("sync") is False
    assert by_key["JWT_SECRET_KEY"].get("generateValue") is True


def test_the_blueprint_is_a_safe_production_configuration() -> None:
    by_key = {v["key"]: v for v in _services()["talign-api"]["envVars"]}
    assert by_key["ENVIRONMENT"]["value"] == "production"
    assert by_key["DEBUG"]["value"] == "false"
    assert by_key["COOKIE_SAMESITE"]["value"] == "lax"  # same-site through the proxy: no SameSite=None
    assert _services()["talign"]["envVars"][1] == {"key": "NEXT_PUBLIC_API_URL", "value": "/api/v1"}


def test_every_backend_variable_in_the_blueprint_is_a_real_setting() -> None:
    from app.core.config import Settings

    real = {name.upper() for name in Settings.model_fields}
    named = {v["key"] for v in _services()["talign-api"]["envVars"]}
    unknown = sorted(named - real - NOT_BACKEND_SETTINGS)
    assert not unknown, f"render.yaml sets variables the backend does not read: {unknown}"


def test_the_production_image_migrates_before_it_serves_and_does_not_reload() -> None:
    text = DOCKERFILE_PROD.read_text(encoding="utf-8")
    cmd = next(line for line in text.splitlines() if line.startswith("CMD"))
    assert cmd.index("alembic upgrade head") < cmd.index("uvicorn")
    assert "--reload" not in text
    assert ".[dev]" not in text
    assert "${PORT}" in cmd  # the host assigns the port
