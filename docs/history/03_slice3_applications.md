# 03 — Slice 3: Candidate Application Flow

## Purpose

The complete deterministic Candidate -> Application -> Job domain flow
that Slice 4's Resume Intelligence Agent will build on top of. Public
job browsing, candidate application submission, a candidate dashboard,
and a recruiter pipeline view — with Application owning all pipeline
state, exactly as specified.

## What was built

```
backend/app/
├── models/
│   └── application.py       Application, ApplicationStatus
├── domain/events.py           + 5 Application events (extends Slice 2's file)
├── repositories/
│   ├── application_repository.py
│   └── job_repository.py     + get_by_id (unscoped), list_open (public)
├── services/
│   ├── application_service.py  submission + state machine + pipeline reads
│   └── job_service.py           + list_open_jobs, get_open_job (public)
├── schemas/application.py
├── api/v1/
│   ├── applications.py        candidate + recruiter routes, one router
│   └── public_jobs.py          NEW — no-auth job browsing
└── alembic/versions/
    └── ..._slice3_applications.py

frontend/src/
├── features/applications/     types, api, hooks, MyApplicationsList,
│                                 PipelineView, ApplyButton
├── features/jobs/               + publicJobsApi, usePublicJobs, usePublicJob
└── app/
    ├── (public)/careers/        NEW route group — no auth required
    ├── (protected)/applications/  candidate dashboard
    └── (protected)/pipeline/       recruiter pipeline view
```

## Key architectural decisions

### 1. Candidate = User, not a second identity table

`Application.candidate_id` references `users.id` directly — there is no
separate `Candidate` profile table. This continues the Slice 1 decision
(single `User` table, `account_type` distinguishing internal vs
candidate) rather than reintroducing the Product Book's original
pre-unification schema. The instruction that "Candidate must not contain
application-specific state" holds trivially: `User` has never had a
status/score/stage column, and now `Application` is where those
concepts live. Flagged explicitly here since it's a real architectural
call, not an ambiguity-free continuation.

### 2. The state machine, same pattern as Job, correctly generalized

`ApplicationService._ALLOWED_TRANSITIONS`:

```
APPLIED:    {SCREENING, REJECTED}
SCREENING:  {INTERVIEW, REJECTED}
INTERVIEW:  {OFFER, REJECTED}
OFFER:      {HIRED, REJECTED}
HIRED:      {}
REJECTED:   {}
```

Unlike Job's single linear chain, REJECTED is a second terminal branch
reachable from four different states — so `_TRANSITION_EVENTS` (Job's
single dict keyed by `(current, target)`) becomes two pieces here:
`_FORWARD_TRANSITION_EVENTS` (a dict, one entry per forward step) plus
`_build_event`, which special-cases REJECTED once rather than
duplicating `ApplicationRejected` four times in a dict. Same "private
dict, not a framework" philosophy as Job — just shaped to fit an
outcome with a branch instead of a single line.

Enforced two layers deep, identical split to Job: DB `CHECK` on value
membership only; `_validate_transition` (pure `staticmethod`) is the
sole holder of the transition graph. Tested with the same method as
Job's suite: full cross-product parametrization (8 valid pairs accepted,
28 invalid pairs rejected) plus named tests for skip-a-stage, move-
backward, both terminal states, no-self-transition, and "cannot reject a
HIRED application" specifically (the one case where REJECTED's
usually-permissive reachability has to still respect terminality).

### 3. Domain events: `ApplicationRejected` carries `previous_status`

The only event in this slice with an extra field beyond
`{entity_id, company_id}`. Since REJECTED is reachable from four states,
a future listener (e.g., a Workflow Engine step that drafts a different
rejection-email tone depending on how far the candidate got) needs to
know which stage the rejection happened at — the event type alone
(`application.rejected`) doesn't carry that, so `previous_status` does.
Same "logged, not published" discipline as Slice 2 — nothing consumes
these yet.

### 4. Independence, checked mechanically — extended, not just repeated

`tests/test_application_workflow_independence.py` mirrors Job's `ast`-
based static import check exactly, applied to
`application_service.py`, `application_repository.py`, and
`application.py`. `domain/events.py` was already covered by Slice 2's
independence test and didn't need a second one — the five new event
classes live in the same file, so the existing test already protects
them.

### 5. No DB constraint for "candidate_id must be an actual candidate"

`Application.candidate_id -> users.id` has no CHECK verifying the
referenced user has `account_type='candidate'` — unlike Slice 1's
`ck_users_company_assignment`, this check spans two tables
(`applications.candidate_id` -> `users.account_type`), which plain
`CHECK` constraints can't express without a trigger. A trigger was
considered and explicitly rejected: `ApplicationService` is the only
code path that ever constructs an `Application` (repositories have no
rule-checking of their own, same convention as every prior repository),
so `ApplicationService._assert_valid_candidate` is both the sole
enforcement point and the sole insert point. This is documented as an
accepted, deliberate limitation in the model's own docstring, not
silently skipped.

### 6. Duplicate-application prevention: exactly as specified

`uq_applications_candidate_job` — a `UNIQUE (candidate_id, job_id)`
constraint — is the DB-level guarantee. `ApplicationService.apply()`
checks `exists_for_candidate_and_job` *before* attempting the insert, so
the ordinary path returns a clean `DuplicateApplicationError` (409); the
constraint exists to catch the race a pure pre-check can't (two
concurrent requests both passing the check before either commits) —
last line of defense, not the primary one, same "two-layer" framing used
throughout this project.

### 7. Public job browsing — a necessary addition, not scope creep

Job listing has been internal-only RBAC since Slice 2
(`ADMIN`/`RECRUITER`/`HIRING_MANAGER`). A candidate obviously can't
apply to a job they can't see, so `app/api/v1/public_jobs.py` adds two
routes with **no** `Depends(require_roles(...))` at all — `GET
/public/jobs` and `GET /public/jobs/{id}`, both hard-restricted to
`status=open` inside `JobService.list_open_jobs` /
`JobService.get_open_job`. This wasn't itemized in the Slice 3 brief
explicitly, but the public application flow is impossible without it,
so it's called out here rather than silently added.

### 8. Route ordering matters: `/mine` before `/{application_id}`

`app/api/v1/applications.py` registers `GET /applications/mine` and
`GET /applications/mine/{application_id}` before `GET
/applications/{application_id}` — otherwise Starlette's path-parameter
pattern for the recruiter-facing `{application_id}` route would
capture the literal string `"mine"` as an ID and route candidate
requests to the wrong (and RBAC-mismatched) handler. Verified directly
in this slice's route-registration check (see Verifying section).

### 9. Testability: repository injection, proven with real mocks

`ApplicationService.__init__` accepts optional `application_repository`
and `job_repository` params, defaulting to real ones — a small addition
over `JobService`'s and `AuthService`'s constructors, added specifically
because `apply()`'s duplicate-check and open-job-check are I/O-dependent
(unlike Job's pure `_validate_transition`) and needed real test coverage
without a live database. `tests/test_application_service_rules.py` uses
`unittest.mock.AsyncMock` to verify: successful application creation,
duplicate rejection, rejection of non-open jobs (both DRAFT and CLOSED
cases), rejection of non-candidate accounts, and — a slightly sharper
check — that an invalid-candidate call never even reaches the
repositories (`assert_not_called()`), i.e., the service doesn't do
unnecessary I/O before its own precondition check fails.

### 10. RBAC split for Applications, mirroring Job's read/write pattern

- **Candidate-facing**: `POST /applications`, `GET /applications/mine`,
  `GET /applications/mine/{id}` — `Role.CANDIDATE` only.
  `candidate_id` is always the authenticated caller — never accepted
  from the request body, same "derive identity from the token, not the
  payload" convention as `create_internal_user` in Slice 1.
- **Recruiter read**: `GET /applications` (pipeline), `GET
  /applications/{id}` — `ADMIN`, `RECRUITER`, `HIRING_MANAGER`.
- **Recruiter write**: `POST /applications/{id}/transition` — `ADMIN`,
  `RECRUITER` only, matching Job's write-role split.

## What's deferred

- **Resume upload / Resume Intelligence** — explicitly out of scope per
  your instruction. `Application` has no `alignment_score`, `summary`,
  or resume reference; those arrive with Slice 4's agent, additively.
- **Extended candidate profile fields** (phone, LinkedIn, portfolio,
  current company/title from the Product Book's original `Candidate`
  entity) — not needed by anything built so far; adding them to `User`
  speculatively would be exactly the premature scope CLAUDE.md warns
  against. Revisit when a feature (the candidate profile page, or Resume
  Intelligence wanting portfolio context) actually needs them.
- **Interview entity / scheduling** — `ApplicationInterviewStageEntered`
  fires on the status transition alone; no `Interview` row, meeting
  link, or calendar integration exists yet. That's its own future slice.
- **Workflow Engine / Compass integration on Application events** —
  per instruction, explicitly not wired. The five domain events exist
  and are logged; nothing consumes them.

## Verifying Slice 3

```bash
cd backend && pytest -v
```
**84 tests pass** (33 from Slices 1-2, unchanged, + 51 new):
- 36 transition-graph tests (8 valid + 28 invalid, full cross-product,
  parametrized) + 6 named edge-case tests (skip-stage, backward-move,
  both terminal states, no-self-transition, reject-a-hired-application)
- 7 `apply()` business-rule tests via injected mocks (success path,
  duplicate, job-not-open for both DRAFT and CLOSED, non-candidate
  account, and the "fails before touching the DB" precondition-ordering
  check)
- 1 architectural independence test (Application module: zero imports
  from `workflow_engine`/`agents`/`compass`)

```bash
python3 -c "from app.main import app; print(len(app.openapi()['paths']))"
# -> 18 (11 from Slices 1-2 + 2 public job routes + 5 application routes)
```

Migration cross-checked column-for-column and constraint-for-constraint
against `Base.metadata` — 7 columns, the `UNIQUE(candidate_id, job_id)`
constraint, 3 foreign keys, and the status `CHECK`, all confirmed
present via direct introspection (same method as Slices 1-2).

Route registration confirmed via the built OpenAPI schema:
`/applications/mine` and `/applications/mine/{application_id}` present
as distinct paths from `/applications/{application_id}` — proves the
ordering concern (#8 above) resolved correctly, not just "probably
fine."

```bash
cd frontend && npx tsc --noEmit && npx next build
```
Clean typecheck; production build succeeds across all 13 routes. One
real Next.js 15 requirement surfaced and was fixed during this slice:
`useSearchParams()` in the `/pipeline` page needed a `<Suspense>`
boundary — Next.js refused to statically prerender the shell otherwise.
Fixed by splitting the page into a `Suspense`-wrapped inner component;
this is now the pattern for any future page reading query params.

Manual flow: candidate registers (Slice 1) -> browses `/careers` (no
auth) -> opens a job -> "Sign in to apply" if logged out, "Apply now" if
logged in -> submits -> sees it on `/applications` -> recruiter opens
`/pipeline` -> moves it APPLIED -> SCREENING -> INTERVIEW -> OFFER ->
HIRED, one legal step at a time -> attempting to apply again from the
same candidate account to the same job returns a 409 with a clear
message, not a raw constraint error.

## Next: Slice 4 — Resume Intelligence Agent

The first real AI agent. Candidate uploads a resume on an `Application`;
the agent extracts skills/experience, compares against the Job's
description, and produces an `AlignmentScore` with an explanation —
stored on (or alongside) `Application`, never on `Candidate`/`User` or
`Job`, continuing this slice's central rule. This is also where
`Compass`, `agents/`, and the `LLMProvider` abstraction (all scaffolded
but empty since Slice 0) get their first real implementation.
