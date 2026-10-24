# 08 — Testing and verification

This document explains how Talign is checked, what each kind of check can and cannot catch, and the commands to run them. It is deliberately candid about the gaps, because a testing document that only lists strengths is not useful to the next person.

In one paragraph: there are **373 backend tests** and **162 frontend tests**, plus a type-checker, a linter and a production-build check, all run automatically on every push. They are fast (about five seconds for the backend, about twenty for the frontend) because they use fakes instead of a database or a real language model. That speed has a price, which is the main thing to understand: **no automated test talks to a real PostgreSQL, and none talks to the real Gemini API.** A separate, manual end-to-end toolkit exists to cover the first gap, and the second can only be covered with a real API key.

---

## 1. What runs, and where

| Check | Command | Where it runs | What it proves |
| --- | --- | --- | --- |
| Backend tests (373) | `cd backend && pytest` | Locally and in CI | Business rules, state machines, permissions wiring, AI pipeline orchestration, scoring, architectural boundaries, documentation accuracy |
| Frontend tests (162) | `cd frontend && npm test` | Locally and in CI | Screens render and behave correctly against a fake backend |
| Type-check | `cd frontend && npm run typecheck` | Locally and in CI | The TypeScript is internally consistent |
| Lint | `cd frontend && npm run lint` | Locally and in CI | No code-quality rule violations (ESLint) |
| Production build | `cd frontend && npm run build` | CI only | Every page compiles and the build succeeds |
| End-to-end on a real database | see section 6 | Manually | The real SQL, the real migrations, the real HTTP stack |
| Isolation and permission check | `python tools/sandbox_e2e/verify_isolation.py` | Manually, against a seeded backend | Tenant isolation and role permissions, over real HTTP |

The continuous-integration definition is `.github/workflows/ci.yml`. It runs three independent jobs in parallel on every push to `main` and every pull request: backend tests, frontend type-check plus lint plus tests, and the production build. A newer push to the same branch cancels the older run. At the time of writing, **this workflow had not yet been run on GitHub**; the first push may reveal differences between that environment and the machines it was developed on.

Inside the backend Docker container, run the tests with `docker compose exec backend pytest`. The few tests that check the documentation skip themselves there, because the container only mounts `backend/` and cannot see the repository's `docs/` folder; they run in CI and in an ordinary checkout.

---

## 2. Backend tests

The backend suite lives in `backend/tests/` (49 files). Its guiding idea is that **every service and agent can be built with fake collaborators**, so a test exercises real business logic without a network or a database. A service takes its repositories (and its AI agent, where it has one) as optional constructor arguments; tests pass fakes, production passes nothing and gets the real ones.

The shared test doubles are in `tests/fakes.py`. The most important is `FakeLLMProvider`: you hand it a scripted queue of results, each either a valid object or an exception to raise, and it replays them one per call. That lets a test describe "the first call fails validation, the retry succeeds" or "the provider is down" precisely and repeatably.

What the 373 tests cover, by area:

| Area | Files (examples) | What they pin down |
| --- | --- | --- |
| State machines | `test_job_status_transitions`, `test_application_status_transitions` (44), `test_leave_request_transitions` (22) | Every legal and illegal move between statuses, including terminal states |
| Business rules | `test_application_service_rules`, `test_leave_request_service_rules` (17), `test_communication_service_rules`, `test_employee_service` | Company scoping, duplicates, overlaps, who may do what to whom |
| Resume Intelligence | `test_resume_scoring` (12), `test_resume_intelligence_agent`, `test_resume_analysis_versioning`, `test_pipeline_scores` | The scoring formula and its edge cases; the retry rule; that analyses are append-only |
| Knowledge | `test_knowledge_agent`, `test_knowledge_chunking`, `test_knowledge_confidence`, `test_knowledge_query_service`, `test_knowledge_document_service` (14), `test_knowledge_company_scoping` | Chunking, confidence bands, the relevance floor, citation validation, company isolation |
| Communication | `test_communication_agent`, `test_email_content_safety`, `test_knowledge_content_safety`, `test_knowledge_prompt_safety` | That prompts carry their safety instructions (for example, a rejection never explains why) |
| Compass | `test_compass_capabilities` (12), `test_compass_knowledge_routing` | Routing by role, and that a role cannot reach a capability it does not hold |
| Hire workflow | `test_workflow_engine`, `test_hire_candidate_workflow`, `test_hire_workflow_task`, `test_hire_workflow_api_wiring`, `test_candidate_to_employee_conversion` | The engine, each step, idempotency, the background task, the account conversion |
| Security | `test_security`, `test_config_safety` (21), `test_login_rate_limiter` (11), `test_login_route_throttling`, `test_unhandled_error_cors` | Tokens and hashing; that deployed environments refuse unsafe settings; throttling; that crashes still carry CORS headers |
| API wiring | `test_public_jobs_api`, `test_leave_request_api_wiring`, `test_knowledge_api_wiring`, `test_health` | Routes, status codes and permissions, using FastAPI's test client with the service layer replaced |
| Documentation | `test_docs_match_code` (7) | The documents agree with the code (section 5) |
| Deployment | `test_deployment_files` (6), `test_database_url` (12) | The blueprint's rewrite rules equal the shared rules file; secrets are never typed into a committed file; every variable named in `render.yaml` is real; the production image migrates before serving; connection strings from a host are translated correctly |

### Tests that guard the architecture

Some tests do not run the code at all. They read the source files as syntax trees and assert structural rules, so a future change that breaks a boundary fails the build even though every behaviour test would still pass:

- Four `*_workflow_independence` tests prove the Job, Application, Leave and Resume Intelligence modules never import the workflow engine, and `test_workflow_engine_independence` proves the engine never imports Compass or an LLM provider.
- `test_candidate_analysis_exposure` proves that no route a candidate can reach is capable of returning analysis content.
- `test_config_safety` proves that a staging or production start refuses the default secret key and debug mode.

---

## 3. Frontend tests

The frontend suite is Vitest with React Testing Library, 16 files and 162 tests, covering the Compass panel (29 tests), leave (24), knowledge (15), the candidate workspace (15), the careers and apply pages (12 and 10), the jobs screens (12), candidate applications (7), the toasts, sign-in form, public header, skill chips and salary formatting.

The testing infrastructure in `frontend/src/test/` is worth knowing about because it decides how trustworthy the tests are:

- `api-mock.ts` is a **fake backend** that answers `fetch` by route and records every call. A test can assert not only what appeared on screen but that *nothing was sent* (`apiMock.writes`), which is how "a hiring manager's click must not mutate anything" style behaviour is checked.
- `render-app.tsx` renders a screen inside the **real providers**, including the real `AuthProvider`, so session handling is exercised and not stubbed.
- `setup.ts` adds a browser-like rule (no focus inside a closed dialog) that jsdom, the simulated browser the tests run in, does not enforce by default. It was added after the first version of the tests could not see a genuine focus bug.

The tests added for deployment cover the rules that are easiest to get dangerously wrong: that an expired token is renewed once and shared between simultaneous requests, that a wrong password is not mistaken for an expired token, that **a write is never repeated automatically** after a network failure (a repeated write could be applied twice), that a sleeping server is waited out only for requests that are safe to repeat, that a real server error is not mistaken for a sleeping one, that the "waking up" screen appears and disappears by itself, and that the id of a dynamic page is read from the address bar in the static build.

The frontend tests were validated by **mutation**: ten deliberate breakages were introduced into the code one at a time, and each was confirmed to make at least one test fail. A test suite that has never been seen to fail proves little.

---

## 4. The two gaps and how each is covered

### The real database

Mocked tests cannot see a whole class of bug. Talign uses async SQLAlchemy, which cannot quietly fetch missing data when code touches an attribute, and which also discards certain columns (every model's `updated_at`) after an UPDATE. Code that returns a just-saved object from a service and then reads one of those attributes raises `MissingGreenlet` (an error meaning "you tried to load data in a context that cannot wait for the database"). With fake repositories this can never happen, so every test passes.

Running the real backend against a real PostgreSQL found three such bugs in one afternoon: every "admin adds a user" call, every leave approval, rejection and cancellation, and the public job list all returned HTTP 500. Each was fixed (the service re-reads the record after saving) and given a regression test that pins the save-then-reload order, but **the tests that pin it are still mocked tests**; only the end-to-end run proves the fix works against the real database.

**The audit is finished.** `tools/sandbox_e2e/audit_update_paths.py` calls **every data-changing endpoint** on a running, seeded backend over real HTTP, in the roles allowed to use each, and fails if any answers a server error. It covers creating, editing, transitioning and deleting jobs; registering, uploading a resume, applying, attaching and re-analysing; drafting, editing, regenerating and sending emails; moving applications through every stage; creating, cancelling, approving and rejecting leave; uploading, re-indexing and deleting knowledge documents; asking Compass; and adding a user. It made 33 calls with **no server error** and no `MissingGreenlet` in the server log, including the paths that had never been exercised before (editing a job, editing and regenerating an email, creating leave). It is rerunnable after any change: run it, and it exits 0 or 1. Its limits: it ran with the stand-in AI, as one user at a time, and it checks that nothing crashes, not that every field of every response is right. The Regenerate button on a hired candidate's *welcome* email, a different bug (an unsupported email type, not a database error), is not part of it; see document 11.

### The real language model

No automated check calls Gemini. The suite proves the plumbing, the rules and the safeguards around the model; it cannot say whether Gemini scores a resume sensibly, writes a good email, or answers a policy question well, and no labelled evaluation set exists. The seeded demo is designed to make quality visible by eye (resumes written to produce a spread of strong, partial and weak matches, and policy documents stating checkable facts), but its first run against a real key is a manual, human judgement.

---

## 5. Tests that keep the documentation honest

Documentation goes stale the moment someone changes the code and forgets the document. A handful of checks prevent that for the facts most likely to drift. They all live in `backend/tests/test_docs_match_code.py`, and each one was proven to fail when its document was deliberately broken:

| Document | What is checked | How |
| --- | --- | --- |
| `04_permissions.md` | The endpoint-by-endpoint access table equals what the route source declares | `scripts/route_access.py` reads the route files as syntax trees; the embedded table must match its output exactly. A second test proves the extractor finds exactly the operations FastAPI publishes. |
| `05_api_reference.md` | Same endpoints, same schemas, same field names as OpenAPI; every endpoint has a note | Structural comparison, not text, so a FastAPI upgrade that only rewords output cannot break it |
| `06_data_model.md` | The data dictionary equals the models; every index named in a migration is mentioned | `scripts/schema_doc.py` renders the SQLAlchemy metadata; migrations are scanned for index names |
| `09_deployment.md` | Every configuration setting in the code is explained | The settings class is enumerated and each name must appear in the document |

The reverse is also true and worth stating: a failing documentation test is not a nuisance, it is the point. It means the code changed and the document describes something that is no longer true.

---

## 6. End-to-end on a real database (manual)

The folder `tools/sandbox_e2e/` is the recipe for running the **real** backend against a **real** PostgreSQL with the pgvector extension, with the two AI providers replaced by deterministic stand-ins (because Google's API is unreachable from a sandbox and a key should not be needed for plumbing checks). It exists so the database-layer bugs described above can be rechecked after any change.

The recipe, without Docker, is in `tools/sandbox_e2e/README.md`: start a database (`pip install pgserver` bundles PostgreSQL with pgvector), set the environment, run `alembic upgrade head`, start `launcher.py` (the real app with stand-in AI), run `scripts/seed_demo.py` to play the whole demo world through the public API, then run `verify_isolation.py`. With Docker, the normal Compose stack already provides the database.

`verify_isolation.py` checks twenty things over real HTTP against the seeded world, among them: each company sees only its own documents, jobs and pipeline; another company's application id answers 404 rather than 403; the public board lists exactly the open jobs with the right employer; a hired employee can read the Knowledge Center but is refused the jobs list; a candidate is refused every staff endpoint; the recruiter cannot approve leave; a hired employee's leave balance shows 2 of 20 days used. When it was run against the seeded stack while writing this document, **all checks passed** (one Compass-citation check is skipped, because the stand-in embeddings cannot produce real citations).

Treat the stand-in AI with care. It fills any requested structure with placeholder values, so every score reads 100 and every drafted email contains placeholder text. That is fine for proving that a request travels through every layer and comes back, and meaningless as evidence of AI quality. Never point it at real data.

---

## 6b. Browser checks of the static site (manual)

`tools/screenshots/verify-static.mjs` drives the production build in a real headless browser, behind `frontend/scripts/serve-export.mjs`, a small server that applies the same rules as Render's static hosting (a file that exists is served first, otherwise the first matching rewrite rule applies) and forwards `/api/*` to the backend. It checks what only a browser can: that the public job list loads through the forwarding; that a deep link to a job opens it; that sign-in lands on the dashboard; that clicking a candidate opens their workspace; that **reloading on a candidate's address keeps the session and the page** (the refresh cookie travelling through the forwarding); that `/jobs/new` is not swallowed by the `/jobs/*` rule; that the refresh cookie is `httpOnly` and scoped to its path; that signing out sends a protected page to the login page; and, in a second phase, the sleeping-server behaviour: with the API switched off a reload shows the "waking up" screen and does **not** sign the visitor out, and switching it back on makes the page recover by itself. All checks passed when run for this documentation.

This proves the application behaves correctly behind a host with Render's *documented* rules. It cannot prove Render's own forwarding behaves as documented, which is why document 09 lists live checks.

---

## 7. What has not been verified

Stated plainly, so nobody assumes otherwise:

- Behaviour against the real Gemini model: score quality, the intended spread across the seeded resumes, email wording, Compass answers and their citations. The first real run needs a human to look.
- Behaviour in real browsers: the redesigned screens, mobile widths, keyboard and screen-reader use, and the ⌘K panel across browsers. The component tests run in a simulated browser.
- The GitHub Actions workflow, which has not yet run on GitHub.
- Production builds with the real Google Fonts download: the sandbox has no route to Google, so the build was run with Next.js's built-in mock for the font request. The static export itself, all 22 pages, was built and driven in a browser; the real font fetch runs in CI and on Render.
- Docker-based startup on a clean machine from this exact repository state.
- Load, performance and concurrency. There is no load test, and the in-memory login throttle and the in-process background tasks assume a single running instance.
- Security review beyond the design rules described in the architecture document: there has been no penetration test and no dependency audit.

---

## 8. How to add a test

Put the rule in the service, not the route, and test the service with fakes. For a new route, add one wiring test that proves the permissions and status codes, using FastAPI's test client with the service replaced. If the change touches the database layer (a new update path that returns the saved object), add a test that pins the reload order *and* run the end-to-end recipe against a real database, because the mocked test alone will always pass. If the change adds or alters an endpoint, a column, a constraint or an index, regenerate the affected document (`python scripts/generate_api_reference.py`, `python scripts/schema_doc.py`, `python scripts/route_access.py --markdown`) and the documentation tests will tell you what to update.
