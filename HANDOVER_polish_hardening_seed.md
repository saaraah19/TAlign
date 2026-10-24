# Handover — polish, hardening, safety net and demo data

Supersedes `HANDOVER_redesign_through_phase6.md` (which covers redesign phases 1-6
and the first polish round; this file covers everything after it).
Read `CLAUDE.md` first (engineering role and principles), then this file, then
inspect the real repo from the attached zip before touching anything.

## Who and how
Sarah, freelance AI automation specialist. Portfolio project, not a client project.
Runs everything locally on Windows/PowerShell via `docker compose up --build`
(a full rebuild, not a restart, after any backend or migration change).
She applies changes by replacing files and live-tests in a real browser; her own
testing is authoritative ("green tests != working system" has proved true again
this session). Working agreement: propose with trade-offs, get sign-off, implement
incrementally, verify, document. No silent scope expansion. Preferences: flowing
prose over bullets, plain-language explanations of technical terms, no unsolicited
visuals. Reply in the language she writes in (French or English). Project docs
and code comments are in English; memory entries are written in French.

## State of the repo
Everything below is in `talign-all-changes-cumulative.zip`
(all changes since her ORIGINAL upload; apply over her checkout, then
`docker compose down && docker compose up --build`).
**One manual step:** delete `frontend/src/features/applications/components/pipeline-view.tsx`
(dead code; a zip cannot delete files; harmless if left).

Verified in the build sandbox at the end of this session:
- backend: 347 tests passing; ruff clean on every file added or changed this session
  (the old baseline noise — B008, SIM102, PIE790, one unused `uuid` import in
  `auth.py` — is untouched on purpose); mypy 48 errors, same count as the original
  (one new instance of the known `acting_user.company_id` UUID|None gap)
- frontend: `tsc --noEmit` clean, ESLint clean (0 problems), 147 Vitest tests passing,
  and a real `next build` passed (all 17 routes) on a copy with only the Google font
  import swapped out (the sandbox cannot reach fonts.googleapis.com)
- a real Postgres 16 + pgvector (via `pip install pgserver`), the real Alembic
  migrations, the real backend, and the demo seed played through the HTTP API
NOT verified: real-browser layout/responsiveness, real Gemini output (scores, drafted
emails, Compass answers), the production Docker setup, anything on Render.

## What changed since the Phase 6 handover (by batch)

### 1. Public jobs and error handling (backend + frontend)
- `/public/jobs` returned 500 on every call: Phase 3 changed `JobListResponse` to carry
  recruiter-only stats, the public route still built it from plain `JobRead`.
  Fix: `PublicJobRead` / `PublicJobListResponse` (no `company_id`, `created_by`, `status`,
  `updated_at`, no stats; ADDS `company_name`, read via `AliasPath("company","name")`).
  `JobRepository.list_open` and the new `get_open_with_company` eager-load `Job.company`
  (`selectinload`); `JobService.get_open_job` uses the latter. Frontend: `PublicJob` type,
  employer name shown on the careers list, job page and apply page.
- The browser showed this as a CORS error because an unhandled 500 skips CORS. The old
  `@app.exception_handler(Exception)` never worked (Starlette runs it in
  `ServerErrorMiddleware`, OUTSIDE CORS; and `debug=True` bypassed it). Replaced by
  `app/core/error_middleware.py::UnhandledExceptionMiddleware`, registered BEFORE
  `CORSMiddleware` in `create_app()` (last added = outermost), so its JSON 500 gets CORS
  headers. `TalignError`/`HTTPException` keep their codes. `TalignError` gained an optional
  `headers` attribute (used for `Retry-After`).

### 2. Hardening (backend)
- `Settings`: `cors_origins` (comma-separated, normalised, `*` and scheme-less refused;
  read via `cors_origins_list`), `cookie_samesite` (`lax`|`strict`|`none`; `none` refused
  with `ENVIRONMENT=local`), `login_max_failed_attempts`, `login_lockout_window_seconds`.
  Startup REFUSES `ENVIRONMENT=staging|production` with the default/short
  (<32 chars) `JWT_SECRET_KEY` or `DEBUG=true` (all problems listed at once).
- Cookies (`app/api/v1/auth.py`) use `settings.cookie_samesite` (was hard-coded `lax`).
  Needed when frontend and API are on different sites (two `*.onrender.com` services).
- `app/core/login_rate_limiter.py`: in-memory, per (client address, lower-cased email),
  default 5 wrong passwords / 15 min, lockout holds even for the right password, success
  resets, injected clock, 429 + `Retry-After`. Deliberately NOT per-address-only (behind a
  misconfigured proxy that would lock the whole site) and NOT shared across instances
  (Redis would be the next step). Needs `FORWARDED_ALLOW_IPS=*` behind a proxy.
- `.env.example` updated (model default aligned with the code: `gemini-2.5-flash`).

### 3. Bugs found only by running against a REAL database (all MissingGreenlet)
Async SQLAlchemy cannot lazy-load on attribute access. The session has
`expire_on_commit=False`, but columns defined with `onupdate=func.now()` (every model's
`updated_at`) are still discarded after an UPDATE, and unloaded relationships are not
loaded at all. Mocked tests can never see this. Found and fixed (each with a test pinning
the commit-then-reload order, mutation-checked):
- `AuthService.create_internal_user` returned the stale instance -> every "admin adds a
  recruiter/hiring manager" was a 500. Now reloads via the repository (eager roles).
- `LeaveRequestService._review` (approve/reject) and `cancel_mine` -> every approve,
  reject and cancel was a 500. Now re-fetch after commit (approve/reject with the employee).
  Verified live on Postgres (approve, reject and cancel).
- `/public/jobs` company name (above): eager load.
**Open risk:** ten models define `updated_at` this way. Any OTHER UPDATE path that returns
the modified instance after `commit()` has the same latent bug. Exercised and fine live:
job transition, application transition, email send, hire workflow, knowledge reindex.
NOT exercised against a real DB: any job edit/PATCH route, onboarding-task completion,
employee updates. Audit those with the seed + `tools/sandbox_e2e/`. A systemic fix would
be `eager_defaults=True` in `__mapper_args__` on those models (one decision, ten models);
the per-service re-fetch is what the project did so far.

### 4. Safety net
- ESLint: `frontend/eslint.config.mjs` (flat config via `FlatCompat`; `npm run lint` used to
  fail because it did not exist). Fixed the 3 real findings (two `<a>` that should be
  `<Link>` on the candidate dashboard; an unused constant).
- Frontend tests: Vitest + Testing Library + jest-dom (`npm test`). Infra in `src/test/`:
  `api-mock.ts` (a fake backend answering `fetch` by route; records calls; `apiMock.writes`
  asserts "nothing was sent"), `render-app.tsx` (real providers incl. the REAL `AuthProvider`;
  `navigate()`), `setup.ts` (dialog polyfill; browser-like "no focus inside a closed
  <dialog>" rule — added because the first version could not see a real focus bug),
  `fixtures.ts`. 13 files / 147 tests; ten deliberate mutations were each caught.
  New devDependencies: vitest, jsdom, @testing-library/react, @testing-library/dom,
  @testing-library/jest-dom, @eslint/eslintrc. The frontend Dockerfile installs from
  `package.json` only (not the lockfile), so the dev image now also installs these.
- CI: `.github/workflows/ci.yml` — three parallel jobs (backend pytest; frontend typecheck +
  lint + tests; production build). The backend job uses `pip install -e ".[dev]"`, which
  FAILED with the full source present ("Multiple top-level packages: app, alembic") — fixed
  with `[tool.setuptools.packages.find] include = ["app*"]` in `pyproject.toml`
  (verified both with full source and with Docker's pyproject-only install step, and in a
  fresh venv). Not yet run on GitHub: the first push may surface environment differences.

### 5. Demo data (`backend/seed_data/`, `backend/scripts/seed_demo.py`)
Run: `docker compose exec backend python scripts/seed_demo.py`
(flags: `--api`, `--no-wait`, `--timeout`, `--pace`). Needs a working `GOOGLE_API_KEY`
for the AI parts (analysis, drafted emails, document embeddings); without it everything else
is still created and the script says which AI steps failed.
Design: plays the world through the PUBLIC HTTP API (not DB writes), so it doubles as a
smoke test of the real product. Idempotent (each step checks first); recognises candidates
already hired (now employees) on re-run. Reset with `docker compose down -v`.
World (all accounts use password `Demo!Pass123`; emails use fictional domains because the
validator rejects reserved ones like `.test`):
- Northwind Robotics (admin Olivia Brown; recruiter Emma Martin; hiring manager David Chen),
  6 documents, 6 jobs (4 open, 1 draft, 1 closed)
- Helix Health (admin Grace Okafor; recruiter Liam Becker), 2 documents (its leave policy says
  25 days vs Northwind's 20, to prove isolation), 2 jobs
- Brightpath Logistics (admin Noah Fischer), empty: the quickest tour of every empty state
- 16 candidates `<first>.<last>@candidates-demo.com` with real PDF/DOCX/TXT resumes written to
  produce a spread: strong, partial, below the experience minimum, vague (exercises
  "insufficient evidence"), an unreadable scanned PDF (Hannah Schmidt), one resume reused for
  two jobs (Daniel Kim, Lina Haddad, Tomás Rivera, Ahmed Benali), 20 applications
- stories: Alex -> interview (+ drafted interview invitation), Fatima -> rejected (rejection
  drafted BEFORE rejecting — the app refuses drafts for rejected applications — then marked
  sent), Wei -> offer, Sarah Lopez -> hired (hire workflow converts her account in place to an
  employee; she then requests leave: one pending, one approved by David, one rejected by Olivia)
Resume/document text is in `resume_content.py` / `knowledge_content.py`; rebuild the files
with `python seed_data/build_assets.py` (needs `pip install reportlab`).
Verified live (twice, then a wipe and a third run): exit 0; second run created nothing;
database counts exact (3 companies, 22 users, 8 jobs, 20 applications, 17 resumes,
8 documents, 1 employee, 3 leave requests, 3 emails); tenant isolation, role permissions,
public board (6 open jobs with the right employer), leave balance (2/20 used) all asserted.
LIMIT: in the sandbox every score read 100 because the stand-in AI marks everything matched;
the intended score spread has never been seen. Check it on the first real run.

### 6. Dev tooling (`tools/sandbox_e2e/`)
`launcher.py` runs the real backend with stand-in AI providers; `verify_isolation.py` asserts
isolation/permissions against a seeded backend; the README is the pgserver recipe. Findings:
sandbox background processes are reclaimed between tool calls (restart the stack inside each
call); `pkill -f` on a pattern also matches your own shell (use `ps | grep "[l]auncher"`);
the shell is `sh` (no `source`, no `<(...)`: wrap in `bash -c`/script files).

### 7. Docs touched
Fixed two stale docstrings (`hire_candidate.py` said three steps; it is FOUR, the last being
`grant_portal_access`; `api/v1/knowledge.py` omitted EMPLOYEE from read access).

## REMAINING WORK, in order

### A. Documentation and README (the planned last step; NOT started beyond fact-gathering)
Existing: `README.md` (151 lines, predates the redesign), `DEMO_WALKTHROUGH.md`, `docs/00-04`
(slices 0-4 only), several `HANDOVER*.md`, `PROJECT_STATUS.md` (stale: says Slice 4).
Goal Sarah stated: document ALL app details and make the README very explanatory, covering all
features. Suggested docs set (derive from code, do not write from memory): product overview and
personas; architecture (backend layers, agents, Compass routing, workflow engine, frontend
structure, design system); feature guide per role; permissions matrix; API reference (generate
from `app.openapi()`: 51 operations); data model; AI system (Resume Intelligence, Knowledge/RAG,
Communication, Dashboard, Compass); testing guide (backend, frontend, e2e tooling, seed);
deployment (below); roadmap/known limits.
Where each fact lives:
- access rules: docstrings atop `backend/app/api/v1/*.py` and the `_READ_ROLES`/`_MANAGE_ROLES`
  constants; Compass capabilities: `backend/app/compass/capabilities.py`
- state machines: `_ALLOWED_TRANSITIONS` in `services/job_service.py` and
  `services/application_service.py` (forward-only; reject from any non-terminal)
- scoring: `backend/app/agents/resume_intelligence/scoring.py` (weights, algorithm version)
- hire workflow: `backend/app/workflow_engine/workflows/hire_candidate.py` (4 steps)
- RAG: `utils/knowledge_chunking.py`, `agents/knowledge/`, knowledge settings in `core/config.py`
- leave: module docstring of `services/leave_request_service.py` (20-day allotment, inclusive
  calendar days, overlap rules, company-wide approval by admin/hiring manager)
- frontend: 17 routes (see any `next build` output); nav per role in `components/nav-bar.tsx`;
  tokens in `tailwind.config.js`; primitives in `src/components/ui/`
- the seed world above doubles as the manual test script for the README ("try it in 10 minutes")

### B. Before deployment (Sarah asked to remember the first one)
1. A dedicated loading screen for when Render wakes a sleeping service (cold start), instead
   of the browser's generic page. Design to decide: the frontend's first API call fails or hangs
   for tens of seconds; show a branded "waking up the server" state with retry/backoff.
2. Env: `ENVIRONMENT=production`, `DEBUG=false`, a random `JWT_SECRET_KEY` (>=32 chars),
   `CORS_ORIGINS=<frontend url>`, `COOKIE_SAMESITE=none` if frontend and API are on different
   sites (or put both behind one domain), `FORWARDED_ALLOW_IPS=*` (so the rate limiter sees real
   client addresses), `GOOGLE_API_KEY`, `DATABASE_URL`/`DATABASE_URL_SYNC`, frontend
   `NEXT_PUBLIC_API_URL`.
3. The frontend Dockerfile runs `npm run dev`; production needs `npm run build && npm start`.
4. Uploaded resumes and knowledge documents are stored on LOCAL DISK (`LOCAL_STORAGE_PATH`),
   which is wiped on every Render redeploy: needs a persistent disk or object storage
   (the Product Book mentions Supabase Storage).
5. Run `alembic upgrade head` on deploy; Postgres needs the `pgvector` extension.
6. Rate limiter is per process (fine for one instance).

### C. Verification only Sarah can do
Real-browser pass over the redesigned screens (candidate journey, leave, jobs, Compass panel,
toasts), including mobile widths; first real-Gemini seed run (check the score spread, drafted
emails, Compass answers with citations); first GitHub Actions run.

### D. Smaller follow-ups
- Audit remaining UPDATE paths for the MissingGreenlet class (see section 3).
- Still on old design details: none in `gray-*` terms (0 left); `PipelineView` is dead code.
- Excluded on purpose (Product Book, outside the MVP): HR-director analytics, notifications,
  interview scheduling/kit, candidate comparison/decision workspace, real email sending
  ("Mark as sent" only records it), rediscovery of past candidates.
- Compass panel: no history across closes; no closing animation.

## Memory
Project memory lives under `/projects/<id>/`: `overview.md` (current state, decisions),
`architecture-decisions.md` (standing learnings incl. the CORS and MissingGreenlet notes),
`ways-of-working.md`. Read them before asking Sarah to repeat context.
