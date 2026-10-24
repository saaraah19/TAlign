# 04 — Slice 4: Resume Intelligence Agent

## Purpose

The first real AI vertical slice — the first implementation behind
Slice 0's `compass/`, `agents/`, and `core/llm_provider.py` scaffolding,
which had sat empty through Slices 1-3. One complete, production-inspired
pipeline: resume upload -> deterministic text extraction -> LLM
structured extraction -> LLM alignment reasoning against
recruiter-authored criteria -> deterministic scoring -> versioned
persistence -> role-scoped exposure through both direct endpoints and
Compass.

## What was built

```
backend/app/
├── models/
│   ├── job.py                + required_skills, preferred_skills, min_years_experience
│   ├── application.py         + resume_id
│   ├── resume.py               NEW — candidate-owned uploaded file
│   ├── parsed_resume.py        NEW — LLM extraction output, reused across applications
│   └── resume_analysis.py      NEW — the alignment analysis; MatchState (3-valued),
│                                 AnalysisStatus, AnalysisProgressStatus (derived, not persisted)
├── agents/
│   ├── resume_intelligence/    NEW — schemas.py, prompts.py, scoring.py, agent.py
│   └── application_status/     NEW — deterministic (zero-LLM) Compass capability
├── compass/
│   ├── compass.py               Compass.handle_message IMPLEMENTED (was NotImplementedError since Slice 0)
│   ├── context_builder.py       NEW — Compass's "build context" step, calls services
│   └── capabilities.py          NEW — idempotent registration, called at app startup
├── repositories/
│   ├── resume_repository.py, parsed_resume_repository.py, resume_analysis_repository.py  NEW
│   └── application_repository.py + job_repository.py  (small additions — unscoped get_by_id)
├── services/
│   ├── resume_service.py        NEW — upload (deterministic) + ensure_parsed (1 LLM call)
│   ├── resume_analysis_service.py  NEW — orchestrates the full pipeline + background task
│   └── application_service.py    + attach_resume
├── core/
│   ├── llm_provider.py           + complete_structured (Slice 4's first real consumer)
│   ├── config.py                  + max_resume_file_size_bytes, allowed_resume_content_types
│   └── exceptions.py              + 7 new domain exceptions
├── utils/
│   ├── local_file_storage.py     NEW — deterministic
│   └── resume_text_extraction.py NEW — deterministic (pypdf/python-docx)
├── api/v1/
│   ├── resumes.py                 NEW
│   ├── compass.py                 NEW
│   ├── applications.py             + 6 endpoints (attach, status x2, analysis, history, reanalyze)
│   └── jobs.py                     + requirement fields passthrough
└── alembic/versions/
    └── ..._slice4_resume_intelligence.py

frontend/src/features/
├── resumes/          NEW — upload, list, ResumePicker
├── compass/           NEW — CompassAsk widget
├── applications/       + AnalysisProgressIndicator, AnalysisDetail, ResumeAttachPanel,
│                          polling hooks (2s interval while parsing/analyzing)
└── jobs/                + required/preferred skills + min_years_experience in JobCreateForm
```

## Key architectural decisions

### 1. The central bet: recruiter-authored criteria, never LLM-inferred

`Job.required_skills` / `preferred_skills` / `min_years_experience` are
the ONLY scoring criteria. `Job.description` is passed to the alignment
prompt labeled explicitly as *context, not criteria* — the prompt text
itself (`prompts.py`) tells the model this in as many words, and no code
path ever converts free text into an official skill list. This is what
makes "reproducible enough that a recruiter can understand why the score
was produced" true rather than aspirational: the checklist is always
knowable and recruiter-visible before any LLM call happens.

### 2. Score computed by OUR code, never the LLM

The LLM's alignment call returns `AlignmentReasoningSchema` —
per-skill `matched`/`not_matched`/`insufficient_evidence` judgments with
evidence, an experience-fit judgment, strengths/concerns/explanation.
**No score field.** `app/agents/resume_intelligence/scoring.py` — zero
LLM calls, a pure function — converts that schema into `overall_score`.
This is the literal implementation of "the LLM provides an analysis and
recommendation, the LLM does NOT make hiring decisions" extended one
level further: the LLM doesn't even make the *scoring* decision, only
the *evidence* decision.

**Methodology** (full detail in `scoring.py`'s own docstring, since that
file is the single source of truth for the algorithm):
- Weights: required 60% / preferred 25% / experience 15%, versioned as
  `SCORING_ALGORITHM_VERSION = "weighted_v1"`.
- Per skill: `matched` = 1.0 point, `insufficient_evidence` = 0.5,
  `not_matched` = 0.0. Insufficient evidence is explicitly **half
  credit** — not proof of absence, not proof of presence, a documented
  value judgment open to revision but never silent revision (a formula
  change bumps the version string).
- A dimension with zero skills (or no `min_years_experience` set) is
  **excluded**, not scored as 0 — remaining weights are normalized
  proportionally: `overall = Σ(pct_i × weight_i) / Σ(weight_i)` over
  included dimensions only.
- `matched_skills`/`missing_skills` (the display lists) are derived from
  the exact same per-skill results used for scoring — they can never
  silently disagree with the number shown.

### 3. Three-valued `MatchState`, not boolean

`MATCHED` / `NOT_MATCHED` / `INSUFFICIENT_EVIDENCE` — one enum, used
both as the persisted column value (`app/models/resume_analysis.py`) and
the LLM structured-output field type
(`app/agents/resume_intelligence/schemas.py` imports it directly from
the model rather than redefining it, so the two can never drift apart).
The alignment prompt explicitly instructs: a skill not mentioned in the
resume must be classified `insufficient_evidence`, never defaulted to
`not_matched` — "absence of evidence is not evidence of absence,"
enforced in the prompt text, not left to model judgment.

### 4. Two LLM calls, two schemas, one agent — and why extraction is reused

`ResumeIntelligenceAgent.extract()` (resume text -> skills/experience,
no job context) and `.reason_alignment()` (extracted resume + job
requirements -> per-skill judgments, no score) are genuinely separate
calls with separate prompts and separate versioning
(`EXTRACTION_PROMPT_VERSION` / `ALIGNMENT_PROMPT_VERSION`). The concrete
reason for the split, beyond "separation of concerns" as an abstract
principle: **a resume only needs to be parsed once.** A candidate with
one resume and five applications should trigger one extraction call and
five job-specific alignment calls, not five redundant extractions of an
identical document. `ResumeAnalysisService.run_analysis` calls
`ResumeService.ensure_parsed`, which checks
`ParsedResumeRepository.get_latest_completed_for_resume` before ever
calling the agent — reuse is the default path, a fresh extraction call
only happens for a genuinely new or previously-failed resume.

### 5. Agent shape: two typed methods, one `run()`, one registry entry

`ResumeIntelligenceAgent` exposes `extract`/`reason_alignment`/`explain`
as direct typed methods (called by `ResumeAnalysisService`, constructing
its own agent instance — bypassing the registry entirely) *and*
implements the base `Agent.run(context)` contract (used only by
Compass's `explain_analysis` capability, delegating to `explain()`).
Both shapes share one LLM-call/versioning setup, so they live on one
agent instance under one registry entry (`name = "explain_analysis"`)
rather than two — documented explicitly in the agent's module docstring
so this doesn't read as an accidental inconsistency with the
one-capability-one-agent pattern `ApplicationStatusAgent` otherwise
follows.

### 6. `ApplicationStatusAgent`: zero LLM, same registry, same routing

Slice 0's `Agent`/`AgentResult` interface never required LLM usage — this
is the first concrete proof. `application_status` is a deterministic
lookup (job title + status, templated), implemented as a real `Agent`
subclass so Compass's routing code (`agent_registry.get(name).run(...)`)
never has to branch on "is this capability AI-backed or not." This is
what makes "keep the capability registry extensible" concrete: adding a
future capability, AI or not, is a new small Agent + one registration
line, never a change to `compass.py` itself.

### 7. Compass implemented, still verifiably lightweight

`Compass.handle_message` — a `NotImplementedError` stub since Slice 0 —
is now real. Its only logic is a role -> capability-name lookup
(`_resolve_capability_for_role`, a pure heuristic since V1 has exactly
one capability per role — no LLM-based intent classification, matching
your explicit V1 scope decision). Everything else is delegation:
`CompassContextBuilder` (a sibling module, not inline in `Compass`)
fetches data via `ApplicationService`/`ResumeAnalysisService`;
`agent.run(...)` produces the answer. Compass never computes a score,
never decides a transition, never touches a repository or the database
directly — checked by inspection here, not mechanically (unlike the
Job/Application independence checks), since "no business logic" is a
qualitative property of what the file *does*, not an import-graph fact
an `ast` scan can verify.

**Not a singleton anymore.** Slice 0's `compass = Compass()` module-level
instance is gone — Compass now needs a request-scoped DB session (to
construct its `CompassContextBuilder`), so it's built fresh per request
(`Compass(db)`), exactly like every `*Service` class in this codebase.

### 8. Candidates never receive analysis content — enforced by shape, not by filtering

No candidate-accessible schema anywhere in this codebase has a score,
skill-match, strength, or concern field. `AnalysisProgressStatusRead`
(the only analysis-adjacent thing a candidate's endpoint ever returns)
has exactly one field: `status`, a coarse enum
(`parsing`/`analyzing`/`complete`/`failed`). This isn't a redaction step
applied to a richer object — the richer object (`ResumeAnalysisRead`) is
never imported by any candidate-facing route function, verified
statically in `tests/test_candidate_analysis_exposure.py` (parses
`applications.py`'s AST and asserts the symbol `ResumeAnalysisRead` is
absent from every candidate-facing function's referenced names).

### 9. `Application.resume_id` is NOT redundant with `ResumeAnalysis.parsed_resume_id`

Raised explicitly for review, resolved as: **keep both.** They answer
different questions that can genuinely diverge — `resume_id` is "what's
currently selected," `ResumeAnalysis.parsed_resume_id` (via
`ParsedResume.resume_id`) is "what was analyzed to produce THIS
historical row." A candidate can swap their attached resume before any
analysis has run (or between an old completed analysis and a fresh one)
— in that gap, `Application.resume_id` is the only source of truth for
"what's current," since there may be zero or a stale `ResumeAnalysis`
row to derive it from.

### 10. Resume attach/re-attach: one code path, not two branches

Per your V1 decision, `ApplicationService.attach_resume` does NOT branch
on "does a completed analysis already exist." Calling this endpoint —
at any point, any number of times — always sets `resume_id` and always
schedules a fresh background analysis run. The endpoint call itself is
"the explicit user action" that authorizes a new version; there is no
implicit or automatic re-analysis anywhere else in the codebase. This
was a deliberate simplification over maintaining two subtly different
behaviors for "first attach" vs "replace an analyzed resume" — same
outcome, one path, one thing to test.

### 11. Failure boundary: `ResumeAnalysis` requires a `ParsedResume` to exist

A failure in the deterministic text-extraction step (corrupt PDF, etc.)
is surfaced via `Resume.status = PARSE_FAILED` and is **not** represented
as a `ResumeAnalysis` row — there is no `ParsedResume` to reference
(`parsed_resume_id` is `NOT NULL`), and creating one artificially would
misrepresent that the pipeline reached the LLM stage at all. Every
failure *after* a `ParsedResume` exists (even a `FAILED` one — LLM
provider error or malformed extraction) *is* persisted as a
`ResumeAnalysis(status=FAILED, error_message=...)` row, since at that
point there's a real attempt with real provenance to record.
`ResumeAnalysisService.get_progress_status` derives the composite
frontend-facing status (`parsing`/`analyzing`/`complete`/`failed`) by
checking `Resume` -> `ParsedResume` -> `ResumeAnalysis` in that order,
so the UI never needs to know this internal distinction — it just polls
one status field.

### 12. Retry policy: one re-prompt for malformed output, never for provider failure

`ResumeIntelligenceAgent._complete_structured_with_retry` retries
**exactly once**, and only on `InvalidStructuredOutputError` (a
re-prompt asking the model to correct its own formatting — a legitimate,
common pattern). `LLMProviderError` (network/timeout/rate-limit)
propagates immediately, no retry. This is a deliberately narrow
exception to "no automatic retry loop in V1" — that instruction is about
background-job-level retry queues (Celery-style backoff), which this
codebase has none of anywhere; a single in-call re-prompt for a
parseable-but-wrong response is a different, smaller thing, and is
documented as such in the agent's own docstring to avoid the two being
conflated later.

### 13. PII minimization: best-effort, documented as such

Neither prompt ever includes `User.first_name`/`email`/any account
field — only resume text and job requirements. Resume text itself may
still contain the candidate's name (most resumes open with one); full
redaction from free-text content is a real NLP problem outside this
slice's scope. `prompts.py`'s docstring says this plainly rather than
implying a guarantee that doesn't exist. The fairness instructions
(`_FAIRNESS_INSTRUCTIONS`, shared by both prompts) explicitly list every
protected/sensitive characteristic from your instruction #10 and tell
the model to ignore them entirely if present in the resume text.

## What's deferred (per explicit scope control)

Semantic skill taxonomy/embeddings, candidate ranking, automatic
rejection or pipeline movement by the agent, candidate rediscovery, OCR,
Communication Agent integration, Workflow Engine integration on
`ResumeAnalysis`/`ParsedResume` events (none were even added — Slice 4
has no new `DomainEvent` subclasses, since nothing downstream reacts to
resume-intelligence completion yet), autonomous hiring decisions, complex
analytics, LLM-based Compass intent classification, partial-credit skill
matching, education/certification scoring, `PromptTemplate` DB-driven
prompt management, and (unavoidably, per Slice 0's original note) a
verified `GeminiProvider` implementation — see section H below.

## H. Testing strategy — what "verified without live Gemini" means here

This sandbox has no network path to `generativelanguage.googleapis.com`
regardless, so `GeminiProvider.complete`/`complete_structured` remain
`NotImplementedError` stubs, exactly as Slice 0 left them. Every other
piece of the pipeline is fully implemented and tested:

- **`tests/fakes.py`**: `FakeLLMProvider`, a real `LLMProvider`
  implementation accepting a queue of canned responses or exceptions —
  injected wherever the codebase accepts a provider, via the same
  dependency-injection pattern already established for repositories in
  Slices 1-3.
- **Scoring** (`tests/test_resume_scoring.py`, 12 tests): pure-function,
  zero LLM — all-matched, all-not-matched, insufficient-evidence half
  credit, insufficient-evidence strictly between matched/not-matched,
  missing-dimension exclusion (not zero), weight normalization,
  reproducibility, matched/missing-list derivation consistency,
  algorithm-version persistence, default-weights sum to 100.
- **Agent orchestration** (`tests/test_resume_intelligence_agent.py`,
  8 tests): extraction/alignment provenance, provider-failure-never-
  retried, malformed-output-retried-once-then-succeeds, malformed-
  output-fails-permanently-after-one-retry, explain() grounding and
  provider-failure wrapping.
- **Versioning** (`tests/test_resume_analysis_versioning.py`):
  structural check that `ResumeAnalysisRepository` has no
  update/save/upsert/patch method at all, plus a full mocked-repository
  run of `run_analysis` confirming persistence goes through `create`.
- **Candidate exposure** (`tests/test_candidate_analysis_exposure.py`):
  schema field-set checks + the AST-based static route-function check
  described in section 8 above.
- **Compass capabilities**
  (`tests/test_compass_capabilities.py`, 11 tests): idempotent
  registration, exact per-role capability sets, `Compass`'s own
  role-resolution heuristic.
- **Architectural independence**
  (`tests/test_resume_intelligence_workflow_independence.py`): the same
  `ast`-based static-import check used for Job/Application, extended to
  the Resume Intelligence module — not explicitly required this slice,
  kept for consistency with the established doctrine.

## Verifying Slice 4

```bash
cd backend && pytest -v
```
**120 tests pass** (84 unchanged from Slices 1-3 + 36 new).

```bash
python3 -c "from app.main import app; from app.compass.capabilities import register_default_capabilities; register_default_capabilities(); print(len(app.openapi()['paths']))"
# -> 28 (18 from Slices 1-3 + 3 resume routes + 1 compass route + 6 application analysis/resume routes)
```

Migration cross-checked column-for-column against `Base.metadata` for
all five affected/new tables (`jobs`, `applications`, `resumes`,
`parsed_resumes`, `resume_analyses`).

```bash
cd frontend && npx tsc --noEmit && npx next build
```
Clean typecheck; production build succeeds across all 15 routes,
including the two new dynamic detail pages
(`/applications/[id]`, `/pipeline/[id]`).

Manual flow (once a real `GOOGLE_API_KEY` and a `GeminiProvider`
implementation exist — out of this slice's verified scope, see section H):
recruiter sets `required_skills`/`preferred_skills`/`min_years_experience`
on a job -> candidate uploads a resume -> attaches it to their
application -> polls through Parsing -> Analyzing -> Complete -> recruiter
opens the pipeline detail page, sees the score breakdown by dimension,
matched/missing skills with evidence, strengths/concerns -> asks Compass
"why did this candidate score X" and gets an answer grounded in the
stored analysis -> candidate's own Compass, asked the same question,
only ever answers with their application's pipeline stage.

## Next: Slice 5

Not yet scoped — natural candidates per the deferred list above include
the Communication Agent (drafting outreach referencing an analysis),
Interview scheduling (which `ApplicationInterviewStageEntered`, defined
back in Slice 3, already anticipates), or beginning real Workflow Engine
integration now that a second and third Agent exist alongside Job's and
Application's domain events for it to eventually react to.
