"""
Generates docs/05_api_reference.md from the application's own OpenAPI schema.

OpenAPI is the machine-readable description FastAPI builds from the route
signatures and the Pydantic schemas (the same data behind the interactive
page at /docs). Rendering the reference from it means the document can never
describe an endpoint, field or type that does not exist. What OpenAPI cannot
say — *who* may call each endpoint — is added from scripts/route_access.py,
which reads the access rule straight from the route source.

Usage (from backend/):
    python scripts/generate_api_reference.py            # rewrite the document
    python scripts/generate_api_reference.py --check    # exit 1 if it is stale

tests/test_docs_match_code.py runs the same comparison on every test run, on
*structure* (endpoints, schemas, field names) rather than exact text, so a
FastAPI or Pydantic upgrade that merely changes wording cannot break it.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
OUTPUT = SCRIPTS.parent.parent / "docs" / "05_api_reference.md"

TAG_TITLES = {
    "auth": "Authentication",
    "jobs": "Jobs (staff)",
    "public-jobs": "Public jobs",
    "applications": "Applications",
    "communication": "Emails (on an application)",
    "resumes": "Resumes (candidate)",
    "compass": "Compass",
    "knowledge": "Knowledge documents",
    "dashboard": "Dashboard",
    "leave-requests": "Leave requests",
    "health": "Health",
}

INTRO = """\
# 05 — API reference

> **This file is generated.** It is produced from the application's OpenAPI schema by
> `backend/scripts/generate_api_reference.py` and checked by
> `backend/tests/test_docs_match_code.py`. Do not edit it by hand: change the code, then run
> `python scripts/generate_api_reference.py` from `backend/`.

Talign's API is a JSON REST API. When the backend is running you can also explore and call it
interactively at `http://localhost:8000/docs` (Swagger UI) or read the raw schema at
`http://localhost:8000/openapi.json`. This page is the same information in a form you can read
without running anything, plus a "who may call this" column that the schema itself cannot express.

## Conventions

**Base URL.** Every path below is relative to the backend's address, for example
`http://localhost:8000`. All business endpoints live under `/api/v1`.

**Authentication.** Sign in with `POST /api/v1/auth/login`; the response contains an
`access_token`. Send it on every protected request as `Authorization: Bearer <token>`. The access
token is short-lived (30 minutes by default). Sign-in also sets an `httpOnly` refresh cookie
(path `/api/v1/auth`) that `POST /api/v1/auth/refresh` exchanges for a new access token.

**Access.** The "Access" line of each endpoint says who may call it: a list of roles, "any
signed-in user" (a valid token and no particular role), or "public" (no token). A caller without
the required role receives `403`; a missing or invalid token receives `401`. Records belonging to
another company are reported as `404`, never `403`.

**Errors.** Domain errors return `{"detail": "<human-readable message>"}` with the status code
that fits the error: `401` authentication, `403` permission, `404` not found (including "not
yours"), `409` conflict (duplicate, already done, overlapping), `422` invalid input or an illegal
state change, `429` too many failed logins (with a `Retry-After` header), `502` the AI provider
failed or answered unusably, `500` an unexpected error. Malformed request bodies are rejected by
FastAPI with `422` and a `detail` list describing each problem.

**Lists.** List endpoints that page results accept `page` (from 1) and `page_size`, and return the
page's `items` together with `total`, `page` and `page_size`.

**IDs and dates.** Identifiers are UUIDs. Timestamps are ISO 8601 in UTC. Dates (leave requests,
hire dates) are `YYYY-MM-DD`.

**Counts.** {operations} operations across {tags} areas, using {schemas} schemas.
"""


# --------------------------------------------------------------------- endpoint notes
#
# OpenAPI knows the shape of every request and response but not what an endpoint *means*, and
# most handlers have no docstring. These notes are the one hand-written part of the reference.
# tests/test_docs_match_code.py fails if an endpoint exists without a note here, so a new route
# cannot ship undocumented. Keyed by "METHOD full-path".

ENDPOINT_NOTES: dict[str, str] = {
    "GET /api/v1/health": "Liveness check. Reports whether the API is up and the database reachable (`status`, `database`).",
    "POST /api/v1/auth/register/company": "Creates a company and its first user, an `admin`, then signs them in (access token in the body, refresh cookie set). `409` if the email is already registered.",
    "POST /api/v1/auth/register/candidate": "Creates a candidate account (no company; it can apply to jobs at any company) and signs it in. `409` if the email is already registered.",
    "POST /api/v1/auth/login": "Checks email and password and signs the user in: returns an access token and sets the refresh cookie. `401` for wrong credentials or a disabled account. After 5 failed attempts within 15 minutes for the same client address and email, further attempts are refused with `429` and a `Retry-After` header, even with the correct password.",
    "POST /api/v1/auth/refresh": "Exchanges the refresh cookie for a new access token. `401` if the cookie is missing, invalid or expired, or the account is no longer active.",
    "POST /api/v1/auth/logout": "Clears the refresh and session cookies. Always succeeds, even when already signed out.",
    "GET /api/v1/auth/me": "Returns the signed-in user: id, company, account type, status and roles.",
    "POST /api/v1/auth/internal-users": "An admin adds a user to their own company with an initial password. `role` must be `admin`, `recruiter`, `hiring_manager` or `employee` (`422` for an unknown role or `candidate`). `409` if the email is taken. Note: a user created with the `employee` role this way has no employee record, so leave endpoints answer `404` for it; only the hire workflow produces a fully working employee.",
    "POST /api/v1/jobs": "Creates a job in the caller's company. It starts as a `draft`. The three scoring criteria (`required_skills`, `preferred_skills`, `min_years_experience`) are what candidates are scored against.",
    "GET /api/v1/jobs": "Lists the company's jobs, newest first, each with applicant statistics. Optional `status` filter; paged.",
    "GET /api/v1/jobs/{job_id}": "One job of the caller's company. `404` if it does not exist or belongs to another company.",
    "PATCH /api/v1/jobs/{job_id}": "Partially updates a job's editable fields (title, description, type, location, salary, skills and experience criteria). It cannot change the status; use the transition endpoint. The frontend has no screen for this yet.",
    "DELETE /api/v1/jobs/{job_id}": "Deletes a job. Only a `draft` can be deleted (`422` otherwise); a published job is closed and archived instead.",
    "POST /api/v1/jobs/{job_id}/transition": "Moves a job one step along `draft`, `open`, `closed`, `archived` (no skipping, no going back). `422` for an illegal move.",
    "GET /api/v1/public/jobs": "The public job board: every `open` job across all companies, newest first, with the employer's name. No sign-in. Paged.",
    "GET /api/v1/public/jobs/{job_id}": "One public job. `404` unless the job is `open`. Internal fields (creator, status, applicant statistics, company id) are never included.",
    "POST /api/v1/applications": "A candidate applies to a job. The job must be `open` (`422` otherwise) and the candidate can apply to a given job only once (`409`). Returns the new application; attach a resume afterwards.",
    "GET /api/v1/applications": "Staff view of the company's pipeline: applications with candidate, job and alignment score. Optional `job_id` and `status` filters; paged (up to 100 per page).",
    "GET /api/v1/applications/mine": "The signed-in candidate's own applications, with job and employer. Paged.",
    "GET /api/v1/applications/mine/{application_id}": "One of the candidate's own applications. `404` for anyone else's.",
    "PUT /api/v1/applications/mine/{application_id}/resume": "Attaches (or replaces) one of the candidate's own resumes on their application and starts the automated analysis in the background. `404` if the resume is not theirs.",
    "GET /api/v1/applications/mine/{application_id}/analysis-status": "The progress of the automated review for the candidate's own application: `not_started`, `parsing`, `analyzing`, `complete` or `failed`. Progress only, never analysis content.",
    "GET /api/v1/applications/{application_id}": "Staff detail of one application, including the candidate's basic information. `404` for another company's application.",
    "POST /api/v1/applications/{application_id}/transition": "Moves an application one step forward (`applied`, `screening`, `interview`, `offer`, `hired`) or rejects it from any stage before the end. `hired` and `rejected` are final. Moving to `hired` starts the hire workflow in the background. `422` for an illegal move.",
    "GET /api/v1/applications/{application_id}/hire-workflow": "The outcome of the hire workflow for a hired application: the workflow run (success, failed or skipped, with the failing step), the employee record and the onboarding tasks. Each is `null` or empty until it exists, so a client can poll.",
    "GET /api/v1/applications/{application_id}/analysis": "The latest completed resume analysis: overall score, the three dimension percentages, per-skill results with evidence, strengths, concerns, explanation and provenance. `404` if none is completed yet.",
    "GET /api/v1/applications/{application_id}/analysis/history": "Every analysis ever run for the application (including failed ones), newest first. Analyses are never overwritten.",
    "GET /api/v1/applications/{application_id}/analysis-status": "The same progress states as the candidate's version, for staff.",
    "POST /api/v1/applications/{application_id}/reanalyze": "Starts a fresh analysis of the attached resume in the background and returns `202` with the current progress. A new analysis row is added; nothing is overwritten.",
    "POST /api/v1/applications/{application_id}/emails/draft": "Drafts an email of the requested type with the AI. Idempotent: if a draft of that type already exists it is returned and no new model call is made. `409` if the application is already `hired` or `rejected`, so draft a rejection before rejecting. Nothing is sent.",
    "POST /api/v1/applications/{application_id}/emails/{email_id}/regenerate": "Replaces a draft's subject and body with a fresh AI draft. `409` if the email was already sent. Known issue: it does not yet support `onboarding_welcome` drafts (see docs/11).",
    "PATCH /api/v1/applications/{application_id}/emails/{email_id}": "Manually edits a draft's subject and body (no AI call). `409` if the email was already sent.",
    "POST /api/v1/applications/{application_id}/emails/{email_id}/send": "Records that the recruiter has sent the draft. Talign sends no email itself. A sent email is permanently read-only (`409` if already sent).",
    "GET /api/v1/applications/{application_id}/emails": "All drafted and sent emails for the application.",
    "POST /api/v1/resumes": "A candidate uploads a resume as a multipart `file` (PDF, DOCX or plain text, up to 5 MB; `422` for another file type or a file that is too large). Text is extracted immediately without AI; the result's status is `text_ready` or `parse_failed` (for example a scanned PDF).",
    "GET /api/v1/resumes/mine": "The signed-in candidate's own resumes.",
    "GET /api/v1/resumes/mine/{resume_id}": "One of the candidate's own resumes. `404` if it belongs to someone else.",
    "POST /api/v1/compass/ask": "Asks Compass a question. What it can answer depends on the caller's role and on `application_id`: candidates get the stage of their own application; employees get company-policy answers; staff get an explanation of the given application's stored analysis, or a policy answer when no application is given. The answer names the `capability_used`; policy answers include citations and a confidence level.",
    "POST /api/v1/knowledge/documents": "An admin uploads a company document as multipart `file`, `title` and `category` (PDF, DOCX or TXT, up to 20 MB). Text extraction and chunking happen in the request; embedding continues in the background, so the returned status is not yet `ready`.",
    "GET /api/v1/knowledge/documents": "The company's knowledge documents with their processing status. Optional `category` filter; paged.",
    "GET /api/v1/knowledge/documents/{document_id}": "One knowledge document with its status and any processing error.",
    "DELETE /api/v1/knowledge/documents/{document_id}": "An admin deletes a document and everything derived from it (its chunks and embeddings).",
    "POST /api/v1/knowledge/documents/{document_id}/reindex": "An admin re-runs extraction, chunking and embedding for a document (for example after a failure or a change of embedding model).",
    "GET /api/v1/dashboard": "Everything the recruiter dashboard shows: the cached daily brief (or `null` if it could not be generated), the open-jobs, active-candidates and pending-actions figures, the stage counts for the funnel, and the lists of applications awaiting review, low-applicant jobs, recent analyses, recent hire-workflow runs and pending draft emails (each capped at 10).",
    "POST /api/v1/leave-requests": "An employee requests leave (`start_date`, `end_date`, `leave_type`, optional `reason`). `422` if the end is before the start; `409` if it overlaps a pending or approved request of theirs; `404` if the account has no employee record.",
    "GET /api/v1/leave-requests": "The company's leave requests for approval, with the employee's details. Optional `status` filter; paged.",
    "GET /api/v1/leave-requests/mine": "The signed-in employee's own leave requests. Paged.",
    "GET /api/v1/leave-requests/mine/balance": "The employee's balance for a calendar year (`year`, default the current year): the fixed annual allotment (20 days), days used by approved requests (calendar days, both ends inclusive) and days remaining, which can be negative.",
    "POST /api/v1/leave-requests/{leave_request_id}/cancel": "An employee cancels their own pending request. Final: `422` if it is no longer pending.",
    "POST /api/v1/leave-requests/{leave_request_id}/approve": "An admin or hiring manager approves a pending request in their company. Final: `422` if it is no longer pending. Approval is allowed even past the employee's allotment.",
    "POST /api/v1/leave-requests/{leave_request_id}/reject": "An admin or hiring manager rejects a pending request in their company. Final: `422` if it is no longer pending.",
}

# --------------------------------------------------------------------- rendering helpers


def _ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def _type_of(schema: dict) -> tuple[str, bool]:
    """(readable type, accepts-null). Understands $ref, anyOf, arrays, enums and formats."""
    if "$ref" in schema:
        return f"`{_ref_name(schema['$ref'])}`", False
    if "anyOf" in schema or "oneOf" in schema:
        options = schema.get("anyOf") or schema.get("oneOf")
        nullable = any(o.get("type") == "null" for o in options)
        parts = [_type_of(o)[0] for o in options if o.get("type") != "null"]
        return " or ".join(parts) if parts else "null", nullable
    if "allOf" in schema and len(schema["allOf"]) == 1:
        return _type_of(schema["allOf"][0])
    kind = schema.get("type")
    if kind == "array":
        inner, _ = _type_of(schema.get("items", {}))
        return f"list of {inner}", False
    if "enum" in schema:
        return "one of " + ", ".join(f"`{v}`" for v in schema["enum"]), False
    if kind == "object":
        return "object", False
    if kind == "string":
        fmt = schema.get("format")
        return f"string ({fmt})" if fmt else "string", False
    if kind:
        return kind, False
    return "any", False


def _constraints(schema: dict) -> list[str]:
    notes: list[str] = []
    inner = schema
    if "anyOf" in schema:  # constraints sit on the non-null branch
        for option in schema["anyOf"]:
            if option.get("type") != "null":
                inner = option
                break
    for key, label in (
        ("minLength", "min length"),
        ("maxLength", "max length"),
        ("minimum", "min"),
        ("maximum", "max"),
        ("minItems", "min items"),
        ("maxItems", "max items"),
    ):
        if key in inner:
            notes.append(f"{label} {inner[key]}")
    if "default" in schema and schema["default"] is not None:
        notes.append(f"default `{schema['default']}`")
    description = schema.get("description")
    if description:
        notes.append(" ".join(description.split()))
    return notes


def _first_paragraph(text: str | None) -> str:
    if not text:
        return ""
    paragraph = re.split(r"\n\s*\n", text.strip(), maxsplit=1)[0]
    return " ".join(paragraph.split())


def _escape(text: str) -> str:
    return text.replace("|", "\\|")


def _schema_fields(schema: dict) -> list[tuple[str, str, bool, str]]:
    """(field, type, required, notes) for an object schema."""
    required = set(schema.get("required", []))
    rows = []
    for name, prop in schema.get("properties", {}).items():
        type_text, nullable = _type_of(prop)
        if nullable:
            type_text += " (or null)"
        rows.append((name, type_text, name in required, "; ".join(_constraints(prop))))
    return rows


def _render_schema(name: str, schema: dict) -> list[str]:
    lines = [f"#### `{name}`", ""]
    # Schema docstrings are written for developers ("see module docstring", internal slice
    # numbers), so they are deliberately not copied into the public reference.
    if "enum" in schema:
        values = ", ".join(f"`{v}`" for v in schema["enum"])
        lines += [f"One of: {values}.", ""]
        return lines
    rows = _schema_fields(schema)
    if not rows:
        lines += ["(no fields)", ""]
        return lines
    lines += ["| Field | Type | Required | Notes |", "| --- | --- | :---: | --- |"]
    for field, type_text, required, notes in rows:
        lines.append(
            f"| `{field}` | {_escape(type_text)} | {'yes' if required else ''} | {_escape(notes)} |"
        )
    lines.append("")
    return lines


def _body_schema_name(operation: dict) -> str | None:
    content = operation.get("requestBody", {}).get("content", {})
    for media in content.values():
        schema = media.get("schema", {})
        if "$ref" in schema:
            return _ref_name(schema["$ref"])
    return None


def _render_operation(method: str, path: str, op: dict, access: str) -> list[str]:
    lines = [f"### `{method} {path}`", ""]
    note = ENDPOINT_NOTES.get(f"{method} {path}")
    if note:
        lines += [_escape(note), ""]
    else:  # tests/test_docs_match_code.py fails before this can ship
        lines += [f"{op.get('summary', '')}.", ""]
    lines += [f"**Access:** {access}", ""]

    params = op.get("parameters", [])
    if params:
        lines += ["| Parameter | In | Type | Required | Notes |", "| --- | --- | --- | :---: | --- |"]
        for p in params:
            type_text, nullable = _type_of(p.get("schema", {}))
            if nullable:
                type_text += " (or null)"
            notes = "; ".join(_constraints(p.get("schema", {})))
            lines.append(
                f"| `{p['name']}` | {p['in']} | {_escape(type_text)} | "
                f"{'yes' if p.get('required') else ''} | {_escape(notes)} |"
            )
        lines.append("")

    body = _body_schema_name(op)
    if body:
        lines += [f"**Request body:** `{body}` (JSON)", ""]
    elif "requestBody" in op:
        content = op["requestBody"].get("content", {})
        kinds = ", ".join(content) or "body"
        multipart = [
            _ref_name(m["schema"]["$ref"]) for m in content.values() if "$ref" in m.get("schema", {})
        ]
        lines += [f"**Request body:** {kinds}" + (f" (`{multipart[0]}`)" if multipart else ""), ""]

    responses = []
    for code, response in op.get("responses", {}).items():
        if code == "422":
            continue
        schema = (
            response.get("content", {}).get("application/json", {}).get("schema")
            if response.get("content")
            else None
        )
        shown = _type_of(schema)[0] if schema else (response.get("description") or "no body")
        responses.append(f"`{code}` {shown}")
    if responses:
        lines += ["**Returns:** " + "; ".join(responses), ""]
    return lines


def render() -> str:
    sys.path.insert(0, str(SCRIPTS))
    sys.path.insert(0, str(SCRIPTS.parent))  # so `import app` works without an editable install
    from route_access import collect_route_access

    from app.main import create_app

    spec = create_app().openapi()
    access_by_route = {(r.method, r.path): r.access for r in collect_route_access()}

    def access_text(method: str, path: str) -> str:
        access = access_by_route[(method, path)]
        if isinstance(access, tuple):
            return ", ".join(f"`{role}`" for role in access)
        return access

    groups: dict[str, list[tuple[str, str, dict]]] = {}
    for path, item in spec["paths"].items():
        for method, op in item.items():
            tag = (op.get("tags") or ["other"])[0]
            groups.setdefault(tag, []).append((method.upper(), path, op))

    schemas = spec["components"]["schemas"]
    operations = sum(len(v) for v in groups.values())

    intro = (
        INTRO.replace("{operations}", str(operations))
        .replace("{tags}", str(len(groups)))
        .replace("{schemas}", str(len(schemas)))
    )
    out = [intro]
    out.append("## Endpoints\n")
    for tag, entries in groups.items():
        out.append(f"## {TAG_TITLES.get(tag, tag.title())}\n")
        for method, path, op in entries:
            out += _render_operation(method, path, op, access_text(method, path))
    out.append("## Schemas\n")
    out.append(
        "Every request and response shape referenced above. *Required* means the field must be "
        "present; a type marked \"(or null)\" may be sent or returned as `null`.\n"
    )
    for name in sorted(schemas):
        if name == "HTTPValidationError" or name == "ValidationError":
            continue
        out += _render_schema(name, schemas[name])
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    text = render()
    if "--check" in sys.argv:
        current = OUTPUT.read_text(encoding="utf-8").replace("\r\n", "\n") if OUTPUT.exists() else ""
        if current != text:
            print(f"{OUTPUT} is out of date. Run: python scripts/generate_api_reference.py")
            return 1
        print("API reference is up to date.")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"Wrote {OUTPUT} ({len(text.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
