# Talign

**Talign isn't an HR platform with AI. It's an AI platform specialized in HR.**

Talign is an AI-native Talent Operating System. A single AI entry point —
**Compass** — assists recruiters, hiring managers, employees, and
candidates throughout hiring and onboarding, while every consequential
HR decision stays with a human.

Full product vision, personas, and architecture: see [`docs/`](./docs).
Want to see it in action rather than read about it? See
[`DEMO_WALKTHROUGH.md`](./DEMO_WALKTHROUGH.md) for a ~10-minute guided
script that exercises every major feature.

## What makes this different from a typical ATS

**One identity, two chapters.** A candidate applies, gets scored, and — if
hired — that exact same account (same email, same password) converts in
place into an employee account with access to company knowledge, Compass,
and leave requests. There's no separate invite flow and no second login,
because there was never a second identity to create.

**One AI entry point, several specialists behind it.** Users never talk to
"the Resume Agent" or "the Knowledge Agent" directly — they talk to Compass,
which routes the request to whichever specialist actually handles it. Adding
a new capability later means teaching Compass one more route, not exposing
one more chat window.

**AI assists, humans decide.** Every score comes with an explanation, not a
bare number. Every AI-drafted email is a draft — Compass has no code path
that sends an email on its own. Nothing gets auto-hired, auto-rejected, or
auto-approved.

## Features

- **Resume Intelligence Agent** — deterministic parsing → LLM extraction →
  LLM alignment scoring against the job's own requirements → a versioned,
  explainable score with strengths and gaps, never a bare percentage.
- **Knowledge Agent** — retrieval-augmented answers over uploaded company
  documents, always with citations back to the source. Available to
  recruiters and, once hired, to employees.
- **Communication Agent** — drafts interview invitations, rejections, and
  onboarding emails. Every draft is reviewed and sent by a human.
- **Workflow Engine** — deterministic, non-LLM orchestration for
  multi-step business processes. Hiring a candidate runs a four-step
  workflow: create the employee record, generate an onboarding checklist,
  draft a welcome email, and convert the candidate's account into an
  employee account — idempotent end to end, so re-triggering it never
  double-creates anything.
- **Leave management** — a simple fixed-allotment leave system: employees
  request time off, any admin or hiring manager can approve it (this
  codebase has no manager-hierarchy concept, by design), and the balance
  updates immediately.
- **Daily Alignment Brief** — an LLM-generated, per-company-per-day summary
  on the recruiter Dashboard, backed by real counts and degrading
  gracefully if the LLM call fails.
- **Full RBAC** — Admin, Recruiter, Hiring Manager, Employee, and Candidate
  roles, enforced at both the API layer and the database layer.

## Architecture at a glance

```
Talign
├── frontend/    Next.js 15, TypeScript, TailwindCSS
├── backend/     FastAPI, SQLAlchemy, PostgreSQL + pgvector
│   └── app/
│       ├── compass/          the single AI entry point (role-aware)
│       ├── workflow_engine/  deterministic business workflow orchestration
│       ├── agents/           specialized LLM reasoning units (Resume, Knowledge, Communication)
│       ├── api/               HTTP layer
│       ├── services/          business logic
│       ├── repositories/      data access
│       ├── models/            SQLAlchemy models
│       └── core/               config, logging, roles, LLM provider abstraction
└── docs/        product vision + architecture decision records
```

`compass/`, `workflow_engine/`, and `agents/` are first-class top-level
modules, not hidden inside `services/` — they are Talign's core
architectural concept, not implementation detail.

**Clean architecture, consistently applied:** every domain service owns one
responsibility, accepts its repositories as optional injected dependencies
(so it's fully testable without a live database), and every meaningful
state transition (a job's status, an application's stage, a leave
request's approval) is validated two ways — a database constraint and a
service-layer state machine — never just one.

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 15, React, TypeScript, TailwindCSS |
| Backend | FastAPI, Python, SQLAlchemy, Alembic |
| Database | PostgreSQL + pgvector |
| AI | Gemini, via a provider-abstraction layer (swappable) |
| Auth | JWT + refresh tokens, RBAC |
| Infra | Docker Compose |

## Quickstart

```bash
cp .env.example .env        # fill in GOOGLE_API_KEY
docker compose up --build
docker compose exec backend alembic upgrade head   # first run only
```

- Frontend: http://localhost:3000
- Backend health: http://localhost:8000/api/v1/health
- Interactive API docs: http://localhost:8000/docs

If containers conflict on names/ports from a previous run:

```bash
docker compose down
docker rm -f talign-postgres talign-backend talign-frontend   # if needed
docker compose up --build
```

A full Docker rebuild (`down` + `up --build`), not just a restart, is
required after any backend code or migration change.

## Running the tests

```bash
cd backend
pip install -e ".[dev]"
pytest
```

The test suite is fully provider-agnostic — a `FakeLLMProvider` stands in
for Gemini, so the whole suite runs with no API key and no network access.

## Development approach

Talign was built in **vertical slices** — each slice ships database,
backend, API, frontend, and tests together, so the product is always in a
working, demoable state. See [`CLAUDE.md`](./CLAUDE.md) for the full
engineering principles this project follows, and [`docs/`](./docs) for the
product vision and early architecture decision records.

## Status

The MVP — authentication, jobs, the full candidate pipeline, Resume
Intelligence, Communication, Knowledge, the Workflow Engine, and the
recruiter Dashboard — is complete. On top of that, V2's Employee Portal
adds: employee accounts (created automatically on hire, not invited
separately), employee-scoped Knowledge and Compass access, and leave
request management. See [`PROJECT_STATUS.md`](./PROJECT_STATUS.md) for a
more detailed, slice-by-slice account of what's been built and what's
explicitly deferred.
