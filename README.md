# Talign

**Talign isn't an HR platform with AI. It's an AI platform specialized in HR.**

Talign is an AI-native talent operating system: one product that carries a person from *"I found a job I like"* to *"I work here and need a day off"*, with a single AI assistant, **Compass**, helping every role along the way, and with every consequential decision left to a human. A recruiter gets candidates ranked and *explained*. A candidate always knows where their application stands. A new hire doesn't get a second account. An employee gets answers about company policy that cite the document they came from.

It is not an applicant-tracking system with a chatbot bolted on, and it is not a chatbot. It is a working product, built as a portfolio project to show end-to-end engineering: a typed React frontend, a layered Python backend, a PostgreSQL database with vector search, an AI layer designed around explainability and safety, an automated test suite, and documentation that is checked against the code.

![The Talign landing page](docs/assets/screenshots/01-landing.png)

> **About the screenshots in this README.** They are real screenshots of the real application, running on a real database loaded with a seeded demo world and driven by a headless browser. They were taken **without a Gemini key**, using a clearly labelled *demo stand-in* for the AI: a small rule-based program that reads the real resume text and policy passages, so that every screen is structurally realistic. The **wording and the exact scores are not what Gemini would produce**, and nothing here measures AI quality. The tooling that took them is in [`tools/screenshots/`](tools/screenshots/README.md) and can retake them with a real key.

---

## Contents

1. [The idea in four sentences](#the-idea-in-four-sentences)
2. [Try it in ten minutes](#try-it-in-ten-minutes)
3. [A tour in scenarios](#a-tour-in-scenarios)
4. [What each role can do](#what-each-role-can-do)
5. [How the AI works](#how-the-ai-works)
6. [How it is built](#how-it-is-built)
7. [Security and permissions](#security-and-permissions)
8. [Testing and verification](#testing-and-verification)
9. [Running and configuring it](#running-and-configuring-it)
10. [Honest limits](#honest-limits)
11. [Roadmap](#roadmap)
12. [Documentation index](#documentation-index)

---

## The idea in four sentences

**One identity, two chapters.** The person who applies for a job is the same person who, once hired, uses the employee portal: hiring converts their existing account in place, so there is never a second login, and the system remembers who they are.

**AI assists, humans decide.** The AI reads, summarises and drafts. It never hires, rejects or sends anything, and it never produces a number: scores come from ordinary, readable code applied to the AI's judgements.

**Every AI result is explained.** A score comes with the evidence for each skill; an answer about a policy comes with the passage it was taken from; a recommendation comes with its reasoning. If the AI doesn't know, it says so instead of guessing.

**Every role sees only what it should.** Candidates, employees, hiring managers, recruiters and admins each get their own experience, and one company can never see another's data.

---

## Try it in ten minutes

You need Docker. From the repository root:

```bash
cp .env.example .env                  # Windows PowerShell: Copy-Item .env.example .env
# put your GOOGLE_API_KEY in .env (needed for the AI features)
docker compose up --build
docker compose exec backend alembic upgrade head          # create the tables
docker compose exec backend python scripts/seed_demo.py   # load the demo world
```

Open <http://localhost:3000> and sign in with any demo account. Every account uses the password **`Demo!Pass123`**.

| Sign in as | Email | You will see |
| --- | --- | --- |
| Recruiter | `emma.martin@northwind-robotics.com` | The pipeline, scored candidates, drafted emails, the daily brief |
| Hiring manager | `david.chen@northwind-robotics.com` | The same pipeline, read-only, plus leave approvals |
| Admin | `olivia.brown@northwind-robotics.com` | Everything a recruiter sees, plus the Knowledge Center's upload controls |
| Candidate | `alex.johnson@candidates-demo.com` | Their applications and the progress of the automated review |
| Employee | `sarah.lopez@candidates-demo.com` | The employee portal: leave and company knowledge |
| Another company | `grace.okafor@helix-health.io` | A different company, with none of Northwind's data |

The guided tour, [`docs/10_try_it_in_10_minutes.md`](docs/10_try_it_in_10_minutes.md), walks through six stops with the exact questions to ask and what you should see. Without an API key every account, job, application and document is still created, but there will be no scores, drafts or Compass answers.

---

## A tour in scenarios

The pictures below follow nine situations through the product. They are in the order a story would tell them.

### 1. A candidate finds a job and applies

Anyone can browse the open jobs across every company on the platform, with no account. Each card shows the employer, location, salary range and the skills the role requires.

![The public job board](docs/assets/screenshots/02-careers.png)

A job's page has a single action. A signed-out visitor is invited to create an account; a staff member is told only candidate accounts can apply; a candidate goes on to apply.

![A job's page](docs/assets/screenshots/03-job-detail.png)

Applying is one page and one click. The candidate chooses a resume they have already uploaded, or uploads a new one (PDF, Word or plain text, up to 5 MB), and submits. A resume belongs to the candidate rather than to one application, so it is uploaded once and reused.

![The application page](docs/assets/screenshots/04a-apply.png)

Afterwards the candidate follows their applications. They see the *stage* of each one, and on an application's page the *progress* of the automated review (parsing, analysing, complete), but **never the score or anything the AI concluded about them**. That is not a hidden field: no endpoint a candidate can call is able to return analysis content, and a test proves it.

![A candidate's applications](docs/assets/screenshots/04-candidate-applications.png)

![A candidate's application page, with a status-only Compass](docs/assets/screenshots/05-candidate-application.png)

The Compass box on this page is deliberately narrow. For a candidate it can only tell them the stage of their own application, and it makes no AI call at all. A candidate cannot use it to ask about the analysis or about company policy.

### 2. The recruiter's morning

A recruiter signs in to a dashboard that answers one question, *what needs my attention today?* The dark card is the **daily brief**, a short AI-written summary with suggested next actions that link straight to candidates. Below it are the figures that matter, the hiring funnel, and lists of what is waiting: applications to review, jobs with too few applicants, and drafted emails to look at. Everything except the brief is plain database counting, recalculated on every load.

![The recruiter's dashboard](docs/assets/screenshots/06-recruiter-dashboard.png)

The **pipeline** is a board with a column per stage, filterable by job. Each card shows the candidate, the role, how long ago they applied, and the **alignment score**. A candidate can only move one step forward, or be rejected, so each card offers exactly its one legal next move.

![The pipeline board](docs/assets/screenshots/07-pipeline.png)

Jobs are created as drafts and published when ready. A job also carries the **scoring criteria**: the required skills, the preferred skills and the minimum years of experience. These three fields, and nothing else, are what candidates are scored against, so the recruiter stays in control of what "a good match" means.

![The job list](docs/assets/screenshots/11-jobs.png)

![Creating a job](docs/assets/screenshots/12-job-new.png)

### 3. Understanding a candidate, with the reasoning shown

Opening a candidate opens their **workspace**. At the top is the **alignment score**, broken into three bars (required skills, preferred skills, experience), with a plain-language explanation. Below, every required and preferred skill is marked *matched*, *not matched* or *insufficient evidence*, with the supporting line from the resume. Then strengths, potential concerns, and the line that matters most: *"An analytical signal to help you evaluate this candidate, not a hiring decision."*

![A strong match, with the evidence for each skill](docs/assets/screenshots/08-workspace-assessment.png)

A weak match reads very differently, and just as clearly. Here every gap is named, and the reason is on the page.

![A weak match: 15 out of 100, with every gap named](docs/assets/screenshots/08b-workspace-weak-match.png)

The same page is where the recruiter writes to the candidate. Compass drafts an **interview invitation** or a **rejection**; the recruiter edits it, regenerates it, or marks it as sent. Talign never emails anyone: "sent" only records that a human sent it. A rejection is written to say nothing about *why*, with no score and no skill gap.

![A drafted interview invitation](docs/assets/screenshots/09-workspace-communication.png)

The recruiter can also *ask*. The suggested questions, like "Why this score?", are answered from the **stored** analysis, so Compass can explain a result but cannot change it or add a new judgement.

![Asking Compass why a candidate scored as they did](docs/assets/screenshots/10-workspace-compass-explain.png)

### 4. Asking the company's own documents

The **Knowledge Center** holds the company's policies, benefits and procedures. An admin uploads PDF, Word or text files; Talign splits them into passages and indexes them by meaning. Anyone in the company can then ask a question and get an answer **with the exact passage it came from**.

![The Knowledge Center](docs/assets/screenshots/13-knowledge-library.png)

![A policy answer with its source passage](docs/assets/screenshots/14-knowledge-answer.png)

When the documents don't cover a question, Compass says so plainly and suggests asking HR. It is built to prefer "I don't know" over an invented policy: if nothing relevant is found, the language model is not even called.

![When the documents have no answer](docs/assets/screenshots/15-knowledge-no-answer.png)

### 5. One person, two chapters: the hire

This is the most distinctive thing in Talign. Wei Zhang holds an offer. The recruiter moves the application to **Hired**.

![A candidate at the offer stage](docs/assets/screenshots/16-hire-offer-stage.png)

A four-step workflow starts in the background, and the page shows it completing: an employee record is created, an onboarding checklist is created, a **welcome email is drafted** (a draft only), and Wei's login is **converted into an employee account**. It is a fixed process, not an AI deciding things, and it is safe to run twice because every step checks whether its work already exists.

![The hire workflow completing](docs/assets/screenshots/17-hire-workflow.png)

Then Wei signs in with the *same email and password* as before, and the product has changed shape: it is now the employee portal of the company that hired them. There was never a second account.

![The same person, now an employee](docs/assets/screenshots/18-employee-dashboard.png)

### 6. The employee's day, and the manager's decision

An employee requests leave: dates, a type, an optional reason. The balance shows what is used and what remains, the form refuses impossible dates and overlaps, and a pending request can be cancelled.

![An employee's leave page, with a pending request](docs/assets/screenshots/19-employee-leave.png)

Any admin or hiring manager can review requests. Approving is one click; rejecting asks for a confirmation.

![The leave approval queue](docs/assets/screenshots/20-leave-approval.png)

![A request approved](docs/assets/screenshots/21-leave-approved.png)

The employee's balance reflects the decision straight away (here 7 of 20 days used, with the vacation approved).

![The employee's balance after approval](docs/assets/screenshots/22-employee-leave-after.png)

### 7. Walls between roles

A hiring manager can read the whole pipeline but cannot change it. The server enforces that: pressing **Move to Offer** is refused with "You do not have permission to perform this action." (The interface still shows the button to a hiring manager, a known rough edge listed under [Honest limits](#honest-limits). The server is the real gatekeeper.)

![A hiring manager is refused](docs/assets/screenshots/23-hiring-manager-refused.png)

### 8. Walls between companies

Talign is multi-company from the start. Helix Health's admin sees only Helix's own jobs and candidates.

![Another company sees only its own pipeline](docs/assets/screenshots/24-helix-pipeline.png)

When Helix's admin asks the same leave question, the answer is **25 days**, from Helix's own document, while Northwind's answer was 20. Documents are filtered by company *before* anything is ranked, so one company's policies can never leak into another's answers.

![Helix's own answer to the same question](docs/assets/screenshots/25-helix-answer.png)

A brand-new company with no data shows calm, honest empty states instead of broken screens.

![A company with no data yet](docs/assets/screenshots/26-brightpath-empty.png)

### 9. When the input is bad

Not every resume can be read. One demo candidate uploaded a scanned image of a resume. Talign has no OCR (reading text out of pictures), so it says so clearly on the resume ("Could not be read — try uploading it again") instead of guessing, and the candidate can upload a text-based file.

![A scanned resume that could not be read](docs/assets/screenshots/27-unreadable-resume.png)

### 10. When the server is asleep

The public demo runs on a free hosting plan that puts the server to sleep when nobody is using it. The web app is a static site that never sleeps, so it opens instantly, and when the server behind it is still waking up Talign says so instead of showing errors. A signed-in visitor is **not** logged out by the wait, and the page continues on its own when the server answers.

![The screen shown while a sleeping server wakes](docs/assets/screenshots/28-waking-up.png)

---

## What each role can do

| | Candidate | Employee | Hiring manager | Recruiter | Admin |
| --- | :---: | :---: | :---: | :---: | :---: |
| Browse open jobs (no account needed) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Apply, upload resumes, follow own applications | ✓ | | | | |
| See candidates' analyses, the pipeline, email history | | | ✓ | ✓ | ✓ |
| Create and manage jobs | | | | ✓ | ✓ |
| Move candidates, draft and send emails, re-run analyses | | | | ✓ | ✓ |
| Dashboard and daily brief | | | ✓ | ✓ | ✓ |
| Read the Knowledge Center and ask Compass about policy | | ✓ | ✓ | ✓ | ✓ |
| Upload, delete and re-index company documents | | | | | ✓ |
| Request leave, see own balance, cancel own pending request | | ✓ | | | |
| Approve or reject leave | | | ✓ | | ✓ |
| Add a user to the company (API only, no screen yet) | | | | | ✓ |

Screen-by-screen detail is in [`docs/03_features_by_role.md`](docs/03_features_by_role.md), and the exact permission of every endpoint, generated from the code, is in [`docs/04_permissions.md`](docs/04_permissions.md).

---

## How the AI works

Talign uses a language model (Google's Gemini, through LangChain) in a few specific places, and is designed around one rule: **the model reads, summarises and drafts, and the code decides and counts.**

**Resume Intelligence** turns a resume and a job's criteria into the analysis you saw above, in a pipeline of small steps:

1. Text is extracted from the resume with ordinary code (no AI).
2. A first model call structures the resume: skills, experience, education. This result is saved and reused, so re-analysing never pays for it again.
3. A second model call judges *each* required and preferred skill against the resume as *matched*, *not matched* or *insufficient evidence*, quoting the evidence. "The resume simply doesn't say" must not be treated as "the candidate lacks it".
4. **Ordinary code computes the score** from those judgements. Each skill earns 1 point if matched, ½ if there is insufficient evidence, and 0 if not matched; required skills weigh 60, preferred skills 25 and experience 15; a dimension with nothing to score is left out and the remaining weights are renormalised, so a recruiter who skips a field doesn't silently change what 100 means.
5. The analysis is stored, never overwritten, stamped with the model, the prompt version and the scoring-algorithm version. Re-analysing adds a new row.

A worked example, computed by running the real scoring function: a job requires Python, SQL and Docker, prefers AWS and Kubernetes and asks for 3 years. The resume clearly shows Python, SQL and AWS, never mentions Docker, lacks Kubernetes and meets the minimum. The required skills earn 2.5 of 3 points (83%), the preferred 1 of 2 (50%), experience 100%, so the overall score is (83.3 × 60 + 50 × 25 + 100 × 15) ÷ 100 = **77.5**, with Docker flagged as *unknown* rather than *missing*.

**The Knowledge Agent** answers questions from company documents using retrieval-augmented generation: it first retrieves the relevant passages (filtered to the caller's company, ranked by similarity using pgvector), and only then asks the model to answer from those passages alone. The defences are layered, and the first two do not depend on the model behaving: a relevance floor (if even the best passage is too weak, the model is never called and the user gets a plain "I don't have information"), then a grounding prompt, then a check that every citation points at a passage that was really retrieved. Confidence is computed from the retrieval similarity, never from the model rating itself.

**The Communication Agent** drafts rejection, interview-invitation and welcome emails. A rejection never explains why. Every draft is reviewable, editable, and only ever *recorded* as sent by a human.

**The daily brief** is the one AI element on the dashboard: a short summary and up to five suggested actions, written from facts the code has already computed, cached once per company per day, and absent (without breaking the page) if the model call fails.

**Compass** is the single entry point users talk to. It is deliberately a simple router: it works out the caller's role and context, looks up what that role is allowed to use, and routes the question to the right capability. A candidate's Compass cannot explain a score no matter how the question is phrased, because that capability is never registered for candidates.

Everything above is described in detail in [`docs/07_ai_system.md`](docs/07_ai_system.md), including what has **not** been verified: the quality of the real model's output, the retrieval thresholds, and the fairness behaviour have not been evaluated against labelled data.

---

## How it is built

```mermaid
flowchart LR
    Browser["Browser<br/>Next.js 15 app"] -->|"REST + JSON"| API["FastAPI<br/>api/v1 routes"]
    API --> Services["Services<br/>business rules"]
    Services --> Repos["Repositories<br/>database queries"]
    Repos --> DB[("PostgreSQL 16<br/>+ pgvector")]
    API -->|"/compass/ask"| Compass["Compass<br/>router only"]
    Compass --> Agents["Agents<br/>LLM-backed"]
    Services --> Agents
    Services --> Engine["Workflow engine<br/>deterministic steps"]
    Agents --> LLM["Gemini via LangChain"]
```

The backend is split into strict layers, each with one job and a rule about what it may touch: **API routes** authenticate and validate, then call one service; **services** own the business rules and raise domain errors (never HTTP ones); **repositories** are the only code that writes queries; **agents** receive plain data and never a database session; **Compass** is a pure router; the **workflow engine** is deterministic and never calls a model. Several of these boundaries are enforced by tests that read the source code as a syntax tree, so a future edit that breaks one fails the build.

Every service takes its repositories and agents as optional constructor arguments, so tests can pass fakes. That is how the whole backend suite runs in seconds without a database or an API key.

| Layer | Technology |
| --- | --- |
| Frontend | Next.js 15 (App Router), React 18, TypeScript, Tailwind CSS, TanStack React Query, React Hook Form, Zod |
| Backend | Python, FastAPI, SQLAlchemy 2 (async), Alembic migrations, Pydantic |
| Database | PostgreSQL 16 with the pgvector extension (vector similarity search) |
| AI | Google Gemini through LangChain; `gemini-embedding-001` embeddings (768 dimensions) |
| Auth | JWT access tokens, httpOnly refresh cookie, role-based access control |
| Delivery | Docker Compose; GitHub Actions CI |

### Project structure

```
Talign/
├── backend/
│   ├── app/
│   │   ├── api/v1/            HTTP routes (access rules declared here)
│   │   ├── services/          business rules
│   │   ├── repositories/      database queries
│   │   ├── models/            SQLAlchemy tables
│   │   ├── schemas/           request and response shapes
│   │   ├── agents/            resume_intelligence, knowledge, communication, dashboard, application_status
│   │   ├── compass/           the router and capability registry
│   │   ├── workflow_engine/   deterministic multi-step processes (the hire workflow)
│   │   ├── domain/            domain events
│   │   └── core/              config, security, errors, LLM provider, rate limiter
│   ├── alembic/versions/      10 migrations
│   ├── seed_data/, scripts/   the demo world and its seed script; documentation generators
│   └── tests/                 373 tests
├── frontend/src/
│   ├── app/                   18 pages in three groups: public, auth, protected (built as a static site)
│   ├── features/              one folder per business area (jobs, applications, knowledge, leave…)
│   ├── components/            shared UI primitives and the Compass panel
│   └── test/                  fake backend and test helpers
├── docs/                      the documentation set, and docs/assets/screenshots
├── tools/                     sandbox_e2e (real-database checks), screenshots (README images)
├── docker-compose.yml         local development
├── render.yaml                the production blueprint (Render free tier)
└── .github/workflows/ci.yml
```

### The data model, in one paragraph

There is one `users` table for every human; what someone may do comes from roles, and a database constraint guarantees internal accounts have a company while candidate accounts have none. A *candidate* is a user, and *hiring converts that same row*. State lives on the **application** (one candidate, one job), never on the candidate or the job. AI results are append-only and stamped with how they were produced. `company_id` is copied onto child tables so the isolation filter is a direct, cheap comparison. 17 tables in all, documented column by column, from the code, in [`docs/06_data_model.md`](docs/06_data_model.md).

### The API

51 endpoints under `/api/v1`, documented in [`docs/05_api_reference.md`](docs/05_api_reference.md) (generated from the application's own OpenAPI schema, with the permission of each endpoint) and explorable live at <http://localhost:8000/docs> when the backend runs.

---

## Security and permissions

- **Two kinds of token.** A 30-minute access token held only in browser memory (never in `localStorage`), and a 14-day refresh token in an `httpOnly` cookie, invisible to JavaScript and limited to one URL path.
- **The server re-reads the user on every request**, so disabling an account takes effect immediately instead of when its token expires.
- **Sign-in is throttled:** five wrong passwords for one (address, email) pair in fifteen minutes lock that pair out, even for the right password.
- **Company isolation at the query level.** The company always comes from the signed-in account, never from the request, and another company's record answers *not found* rather than *forbidden*, so it doesn't even confirm it exists.
- **Unsafe configuration refuses to start.** In a staging or production environment the backend exits if the secret key is the default or too short, or debug mode is on.
- **Crashes stay legible.** An unexpected error still returns a JSON response with CORS headers, so it is never disguised as a browser CORS problem.

Details, and the generated endpoint-by-endpoint access table, are in [`docs/04_permissions.md`](docs/04_permissions.md).

---

## Testing and verification

| Check | Size | What it proves |
| --- | --- | --- |
| Backend tests | 373 | Business rules, state machines, permissions wiring, AI orchestration, scoring, architectural boundaries |
| Frontend tests | 162 | Screens render and behave correctly against a fake backend, validated by deliberately breaking the code ten ways and confirming tests fail |
| Type-check and lint | | The TypeScript is consistent and clean |
| Documentation and deployment tests | 7 + 18 | The permissions table, API reference, data dictionary and settings list match the code; the deployment blueprint, rewrite rules and connection-string handling are correct. Each was proven to fail when broken |
| End-to-end on a real database | manual | The real SQL and migrations; found three bugs that no mocked test could |
| The production build in a real browser | manual | Deep links, sign-in and reload through the API forwarding, and a sleeping server, driven by a headless browser |

The main thing to understand is the gap, so it is stated plainly: the automated suites use fakes, which makes them fast, but **no automated test talks to a real PostgreSQL or to the real Gemini API**. A manual end-to-end toolkit ([`tools/sandbox_e2e`](tools/sandbox_e2e/README.md)) covers the database; only a human with a real key can judge the AI's quality. GitHub Actions runs everything on each push; that workflow has not yet run on GitHub. Full detail: [`docs/08_testing.md`](docs/08_testing.md).

---

## Running and configuring it

The setup is in [Try it in ten minutes](#try-it-in-ten-minutes). Every setting is explained in [`docs/09_deployment.md`](docs/09_deployment.md); the most important are:

| Variable | Meaning |
| --- | --- |
| `GOOGLE_API_KEY` | Powers every AI feature and document search. Without it, everything else still works |
| `JWT_SECRET_KEY` | Signs sign-in tokens. In staging or production the app refuses to start with the default |
| `ENVIRONMENT`, `DEBUG` | `local` for development; anything else turns on the startup safety checks |
| `CORS_ORIGINS` | The exact web addresses allowed to call the API from a browser |
| `NEXT_PUBLIC_API_URL` | The API's address as the browser sees it. Baked into the frontend at build time |

### Going online

The product is built to be hosted on **Render's free tier**, and the repository contains everything for it: a `render.yaml` blueprint, a production image for the API that applies its own database migrations on start, and a web app built as a **static site**. That last choice is the central one. A static site is served by a CDN and never sleeps, so the only thing that can be asleep is the API, and the app can handle that gracefully (the screen above). The host also forwards `/api` to the API, so the browser only ever talks to one address, which removes the cross-site cookie and CORS problems.

```mermaid
flowchart LR
    Browser["Browser"] --> Static["Static site<br/>CDN, never sleeps"]
    Static -->|"/api/* forwarded"| API["API<br/>Docker web service<br/>sleeps when idle"]
    API --> DB[("PostgreSQL<br/>+ pgvector")]
```

This design is **implemented and tested as far as it can be without Render itself**: the production build was driven in a real browser behind a server applying Render's documented rules, and the API's production start command was run against an empty database. What remains is the first real deployment and a short list of live checks (does Render's forwarding pass the sign-in cookie, how long a wake-up really takes). Step-by-step instructions, those checks, and what the free tier does and does not give you are in [`docs/09_deployment.md`](docs/09_deployment.md). One honest caveat belongs here: free hosting means a database that expires after 30 days, a server that sleeps, and uploaded files that don't survive a restart, all documented, none hidden.

---

## Honest limits

A README that only lists strengths is not useful, so here is what a visitor should know. Each is numbered, with its evidence, in [`docs/11_roadmap_and_known_limits.md`](docs/11_roadmap_and_known_limits.md).

- **The AI's real output quality has not been evaluated.** The seeded resumes are designed to produce a spread of scores, but that spread has not been seen on a real run; the screenshots above come from a stand-in.
- **A defect:** the *Regenerate* button on a hired candidate's welcome-email draft fails with a server error (confirmed on a running stack). Editing and sending it work.
- **Admin-created employees can't use leave.** Only a *hired* candidate becomes a fully working employee. Confirmed on a running stack.
- **Free-tier hosting realities:** the API sleeps after 15 idle minutes (about a minute to wake), the free database expires after 30 days (the demo is re-seedable with one command), and uploaded files do not survive a restart (only re-indexing a document needs them, and it now fails with a clear message).
- **Missing screens:** there is no screen to edit a job after creating it, none to add teammates (API only), and the onboarding checklist created at hire cannot be ticked off.
- **A hiring manager sees buttons the server refuses** (shown above).
- **Scanned PDFs can't be analysed** (no OCR), and the annual leave allowance is a fixed 20 days for every company.
- **Single instance only:** background jobs run inside the web process and the login throttle is in memory.
- **No bias evaluation.** The prompts forbid using protected characteristics and never receive a candidate's name, but resume text often contains one.

The database audit for one class of bug (`MissingGreenlet`, an async-database error that only appears against a real database) is **finished**: three instances were found and fixed earlier, and a repeatable script now exercises every data-changing endpoint on a real database (33 calls, no server error).

---

## Roadmap

In the agreed order: the documentation, then **going online** (built and tested; the first real deployment is next), then **fixing the issues above**. After that, the natural next slices are the ones the original product vision names and the MVP deliberately left out: an analytics view for HR directors, side-by-side candidate comparison, interview scheduling, a real job queue, and email integration. Each would be scoped and agreed before any code is written.

What was left out of the MVP on purpose, and why, is listed in [`docs/11_roadmap_and_known_limits.md`](docs/11_roadmap_and_known_limits.md).

---

## Documentation index

| Document | What it covers |
| --- | --- |
| [`01_product_overview.md`](docs/01_product_overview.md) | What Talign is for, who it serves, the principles behind it, and how much of the vision is built |
| [`02_architecture.md`](docs/02_architecture.md) | Layers, request flow, errors, sessions, Compass, agents, the workflow engine, the frontend, and where the code differs from the original plan |
| [`03_features_by_role.md`](docs/03_features_by_role.md) | Every page and capability, by role |
| [`04_permissions.md`](docs/04_permissions.md) | Roles, rules on top of roles, and a generated endpoint-by-endpoint access table |
| [`05_api_reference.md`](docs/05_api_reference.md) | Every endpoint and schema, generated from the OpenAPI schema |
| [`06_data_model.md`](docs/06_data_model.md) | Tables, relationships, lifecycles, migrations, and a generated data dictionary |
| [`07_ai_system.md`](docs/07_ai_system.md) | How every AI feature works, how it is validated, and what is unverified |
| [`08_testing.md`](docs/08_testing.md) | What is tested, how, and the gaps |
| [`09_deployment.md`](docs/09_deployment.md) | Running it, every setting, what isn't production-ready, the plan for going online |
| [`10_try_it_in_10_minutes.md`](docs/10_try_it_in_10_minutes.md) | The guided tour of the demo world |
| [`11_roadmap_and_known_limits.md`](docs/11_roadmap_and_known_limits.md) | What was left out, 27 known issues with evidence, what happens next |
| [`docs/history/`](docs/history) | The original design notes for each build slice, kept as history |

Four of these documents contain sections that are **generated from the code and checked by tests** (the permissions table, the API reference, the data dictionary and the settings list), so they cannot quietly drift from what the application does.
