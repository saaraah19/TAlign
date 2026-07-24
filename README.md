# Talign

**Talign isn't an HR platform with AI. It's an AI platform specialized in HR.**

Talign is an AI-native Talent Operating System. A single AI entry point —
**Compass** — assists recruiters, hiring managers, employees, and
candidates throughout hiring and onboarding, while every consequential
HR decision stays with a human.

Full product vision, personas, and architecture: see [`docs/`](./docs).

## Status

See [`PROJECT_STATUS.md`](./PROJECT_STATUS.md) for where things currently stand, known gaps, and next steps.

✅ **Slice 0 — Foundation.** Architecture and project scaffolding.
✅ **Slice 1 — Authentication & Identity.** Company/candidate registration,
JWT auth, RBAC. See [`docs/01_slice1_authentication.md`](./docs/01_slice1_authentication.md).
✅ **Slice 2 — Jobs.** Recruiter-facing CRUD with a domain-owned status
state machine (DRAFT → OPEN → CLOSED → ARCHIVED). See
[`docs/02_slice2_jobs.md`](./docs/02_slice2_jobs.md).
✅ **Slice 3 — Candidate Application Flow.** Public job browsing,
candidate applications, recruiter pipeline, with a deterministic
Application state machine (APPLIED → SCREENING → INTERVIEW → OFFER →
HIRED, REJECTED as a terminal branch). See
[`docs/03_slice3_applications.md`](./docs/03_slice3_applications.md).
✅ **Slice 4 — Resume Intelligence Agent.** The first AI vertical slice:
resume upload → deterministic parsing → LLM structured extraction → LLM
alignment reasoning against recruiter-authored criteria → deterministic,
reproducible scoring → versioned analysis, exposed through both direct
endpoints and Compass (implemented for the first time this slice). See
[`docs/04_slice4_resume_intelligence.md`](./docs/04_slice4_resume_intelligence.md).

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

## Quickstart

```bash
cp .env.example .env        # fill in GOOGLE_API_KEY etc. when needed
docker compose up --build
```

- Backend: http://localhost:8000/api/v1/health
- Frontend: http://localhost:3000

## Development approach

Talign is built in **vertical slices** — each slice ships database,
backend, API, frontend, and docs together, so the product is always in a
working, demoable state. See [`CLAUDE.md`](./CLAUDE.md) for full
engineering principles and [`docs/`](./docs) for the product book and
per-slice architecture notes.
