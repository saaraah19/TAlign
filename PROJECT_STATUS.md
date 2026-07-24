# PROJECT STATUS — Talign

_Last updated: end of Slice 4 review._

## Where things stand

Slices 0-4 are complete, approved, and verified (120/120 backend tests
passing, clean frontend typecheck/build). Full per-slice rationale lives
in `docs/00_slice0_foundation.md` through `docs/04_slice4_resume_intelligence.md`.

## Fixed since last update

- **`email-validator` missing dependency**: `pyproject.toml` declared plain
  `pydantic` but `EmailStr` (used in `app/schemas/auth.py`) needs the
  `email-validator` extra. Backend crashed on startup with
  `ImportError: email-validator is not installed`. Fixed:
  `"pydantic>=2.8.0"` -> `"pydantic[email]>=2.8.0"`.

## Known gap: `GeminiProvider` is unimplemented

`app/core/llm_provider.py`'s `GeminiProvider.complete` and
`.complete_structured` are still `NotImplementedError` stubs. The entire
Resume Intelligence pipeline (Slice 4) was built and tested against
`FakeLLMProvider` (`backend/tests/fakes.py`) because the build
environment had no network path to Google's API. **A real API key in
`.env` will not do anything useful until this is implemented.**

This is the immediate next piece of work before Slice 4 can be tested
end-to-end with real Gemini calls.

## How to run locally

```bash
cp .env.example .env        # then set GOOGLE_API_KEY
docker compose up --build
docker compose exec backend alembic upgrade head   # first run only
```
- Backend: http://localhost:8000/api/v1/health
- API docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

## Next steps (unordered, pick one)

1. **Implement real `GeminiProvider`** - needed to actually exercise
   Slice 4 with a live key. Likely uses `google-generativeai`, structured
   output via function-calling or JSON mode, mapped to the
   `LLMProvider.complete_structured` error contract (raise
   `InvalidStructuredOutputError` vs `LLMProviderError` appropriately -
   see that method's docstring in `llm_provider.py`).
2. **Slice 5** - not yet scoped. Candidates per Slice 4's deferred list:
   Communication Agent, Interview scheduling, or Workflow Engine
   integration reacting to the domain events already defined in Job/
   Application (Slices 2-3).

## Engineering conventions established so far

(Full detail in each slice's doc - this is a quick-reference index.)

- Vertical slices: DB + backend + API + frontend + docs together, always
  a working product.
- Two-layer validation: DB `CHECK`/constraints + service-layer domain
  exceptions, for every invariant that matters (company assignment, job
  status transitions, application transitions, duplicate applications).
- State machines are private dicts on the owning service, never a shared
  generic framework.
- Domain events (`app/domain/events.py`) are a shared vocabulary, not an
  event bus - logged, not published, until something real consumes them.
- `Compass` is a pure router; all business logic lives in domain
  services or Agents, never in `compass/`.
- Agents receive plain structured data, never a DB session or service.
- Architectural boundaries (Job/Application/Resume-Intelligence must not
  import `workflow_engine`) are enforced by `ast`-based static tests, not
  just documented.
- Candidate-facing schemas structurally cannot carry internal-only
  fields (verified by tests, not just convention).
