# 00 — Slice 0: Foundation

## Purpose

Establish a production-quality engineering foundation before any business
logic exists. No authentication, no AI implementation, no domain models.
Only: project structure, tooling, and the three first-class AI modules
(`compass/`, `workflow_engine/`, `agents/`) as empty-but-correctly-shaped
skeletons.

The goal is that Slice 1 (Authentication & Identity) starts writing
business code on day one instead of also inventing project structure.

## What was built

```
talign/
├── docker-compose.yml       postgres (pgvector) + backend + frontend
├── .env.example
├── backend/
│   ├── pyproject.toml       uv/pip-installable, ruff + mypy configured
│   ├── alembic.ini + alembic/   migrations wired to async app config
│   └── app/
│       ├── core/            config, logging, roles, LLM provider abstraction
│       ├── database/        SQLAlchemy async engine, session, declarative Base
│       ├── api/v1/          FastAPI router aggregation + /health
│       ├── compass/         Compass orchestrator skeleton (not implemented)
│       ├── workflow_engine/ deterministic workflow runner (not implemented)
│       ├── agents/          Agent base class + registry (empty, no agents yet)
│       ├── models/          empty — Slice 1 adds User, Role, Company
│       ├── schemas/         empty — Slice 1 adds Pydantic schemas
│       ├── services/        empty — Slice 1 adds business logic
│       ├── repositories/    empty — Slice 1 adds data access layer
│       └── main.py          FastAPI app entrypoint
└── frontend/
    ├── package.json         Next.js 15, React Query, RHF, Zod, Tailwind
    └── src/
        ├── app/             App Router — layout.tsx, page.tsx (health check UI)
        ├── lib/              api-client.ts — single fetch wrapper
        └── features/         empty — Slice 1 adds auth/
```

## Key architectural decisions

### 1. Compass, Workflow Engine, and Agents are top-level, not nested in `services/`

This is the platform's core differentiator per the Product Book: users
interact with one intelligence (Compass); internally, a deterministic
Workflow Engine and specialized Agents collaborate. Burying that inside
a generic `services/ai_service.py` would hide the concept that the
entire product is built around. Reflecting it in the folder structure
means anyone opening the repo understands the architecture before
reading a line of business logic.

### 2. Workflow Engine ≠ another agent

Per the CLAUDE.md clarification: the Workflow Engine is a **deterministic
orchestrator**, not an LLM reasoning node. `app/workflow_engine/workflow.py`
enforces this structurally — a `Workflow` subclass implements
`execute_step` with plain Python, and only steps explicitly marked
`requires_agent=True` cause the engine to dispatch to the Agent Registry.
The Workflow Engine itself never imports `LLMProvider`.

This matters because it's the difference between "AI orchestrates
everything" (unpredictable, hard to test, hard to explain to an HR
compliance team) and "business rules are deterministic; AI is invoked
only where reasoning is genuinely required" — which is also explicitly
what CLAUDE.md's AI Principles demand ("Never make irreversible HR
decisions automatically").

### 3. Agent Registry exists before any agent does

`app/agents/registry.py` is a capability-name → `Agent` instance lookup,
populated by nothing in Slice 0. This is intentional: it's what makes
"add an agent later without modifying Compass" actually true rather than
aspirational prose. If we wrote Compass's routing as a hardcoded
if/elif over 3 (or 4, counting the Workflow Engine) known agents, adding
the V2 Interview Agent would mean editing Compass. With the registry,
it means registering a new capability name — Compass's code doesn't
change.

### 4. Compass Capability Registry — role-awareness by construction, not filtering

`app/compass/capability_registry.py` scopes which AI capabilities each
`Role` may invoke. Per your Point 3 (Candidate Compass): a candidate's
Compass must never expose alignment scores or internal notes. The
registry means that capability simply isn't resolvable for
`Role.CANDIDATE` — Compass never constructs a prompt, never calls an
agent, for a capability the role can't reach. This is safer than
generating an internal answer and redacting it, which risks leaking
information through phrasing, timing, or bugs in the redaction step.

### 5. LLM Provider abstraction, Gemini as default

`app/core/llm_provider.py` defines an `LLMProvider` protocol. No other
file in the codebase may import a provider SDK directly — agents depend
on the protocol, injected at construction. `get_llm_provider()` is the
single branch point reading `settings.llm_provider`. Switching from
Gemini to OpenAI or Anthropic later is a one-line config change, not a
refactor across every agent. Nothing calls `.complete()` yet — Slice 0
has no AI implementation per scope; the first real call happens when the
Resume Intelligence Agent is built.

### 6. WorkspaceContext defined early, populated later

`app/compass/context.py` defines the shape of the shared context object
every Compass-invoked capability receives (company, user, role,
workspace, conversation history). The Product Book calls Context
Building "the most underestimated step" in the AI pipeline — agents that
independently re-fetch context drift out of sync. Defining the shape now
(even though nothing populates `.data` yet, since no workspace entities
exist) means the first real agent is built against a stable contract
instead of improvising context-passing ad hoc.

### 7. Single `User` + `Role`/`UserRole` model (not per-role tables)

Not yet implemented (Slice 1), but the `Role` enum in `app/core/roles.py`
already reflects this decision from the Product Book's Domain Model
section: one `User` table, roles attached via a join table, rather than
separate `Recruiter`/`Employee`/`Candidate` tables. This directly enables
Candidate accounts (Point 2) sharing the same auth/session machinery as
internal roles, while `INTERNAL_ROLES` gives a single place to draw the
internal-vs-external boundary for visibility rules (internal notes,
alignment scores).

### 8. Database: async app, sync migrations

The app runs on `asyncpg` at request time (`database_url`), but Alembic
migrations use a sync psycopg2 connection (`database_url_sync`) since
Alembic's migration runner doesn't support async natively. Both URLs are
defined in `core/config.py` so this is a one-time decision, not a
recurring gotcha.

### 9. pgvector from day one

`docker-compose.yml` uses the `pgvector/pgvector:pg16` image rather than
plain `postgres:16`, even though no embeddings exist yet. Per the
Product Book: "no need for a separate vector database for the MVP" — but
that only holds if pgvector is available from the start rather than
retrofitted when the Knowledge Agent ships.

### 10. Local file storage for MVP

Per your Point 5. `settings.storage_provider` is typed as a `Literal`
with only `"local"` today, but shaped so a `StorageProvider` abstraction
(mirroring `LLMProvider`) can be introduced later without touching
calling code — deferred until a real feature (resume upload, Slice 3)
needs it, per CLAUDE.md's "avoid unnecessary abstractions" principle.

## What's explicitly deferred

- Any concrete `Agent` implementation (Resume/Knowledge/Communication)
- Any concrete `Workflow` implementation
- Compass's actual `handle_message` logic (raises `NotImplementedError`
  by design — wiring it against an empty registry would be theater)
- All database models (`User`, `Company`, `Job`, `Candidate`, ...)
- Authentication (JWT issuing/verification, RBAC guards)
- Any real UI beyond a health-check page proving frontend ↔ backend
  connectivity

## Verifying Slice 0

```bash
cp .env.example .env
docker compose up --build
```

- `GET http://localhost:8000/api/v1/health` → `{"status": "ok", "database": "ok"}`
- `http://localhost:3000` → renders backend status
- `cd backend && pytest` → `test_health.py` passes

## Next: Slice 1 — Authentication & Identity

`Company`, `User`, `Role`, `UserRole` models; JWT + refresh token issuing;
RBAC dependency guards in the API layer; registration + login for both
internal roles and Candidate accounts (per your Point 2).
