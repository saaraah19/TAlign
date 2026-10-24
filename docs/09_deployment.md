# 09 — Running and deploying Talign

This document covers three things: how to run Talign on your own machine, every setting that controls it, and how it is put on the internet on Render's free tier. The deployment design is **implemented in the repository and tested as far as it can be without Render** (see section 5 for exactly what was and was not verified), but it has **not yet been run on Render itself**: the live checks in section 6 are what remains.

---

## 1. What runs

Talign is three processes, started together by Docker Compose:

| Service | Image or source | Port | Role |
| --- | --- | --- | --- |
| `postgres` | `pgvector/pgvector:pg16` | 5432 | The database: PostgreSQL 16 with the pgvector extension for similarity search |
| `backend` | `backend/Dockerfile` (Python 3.11, FastAPI served by Uvicorn) | 8000 | The API |
| `frontend` | `frontend/Dockerfile` (Node 20, Next.js dev server) | 3000 | The web application, in development mode |

The database keeps its data in a Docker volume (`talign_postgres_data`) and the backend keeps uploaded files in another (`talign_storage`), so both survive restarts. In this development setup the source folders are also mounted into the containers, so code edits reload automatically. Production is different: the web app is a static site and the API has its own production image (section 6).

---

## 2. Run it locally

You need Docker Desktop (or Docker Engine with the Compose plugin). From the repository root:

```bash
cp .env.example .env            # on Windows PowerShell: Copy-Item .env.example .env
# edit .env: set GOOGLE_API_KEY if you want the AI features (see section 3)
docker compose up --build
docker compose exec backend alembic upgrade head     # create the tables (first run, and after any new migration)
docker compose exec backend python scripts/seed_demo.py   # optional: load the demo world
```

Then open:

- the application at <http://localhost:3000>
- the API's health check at <http://localhost:8000/api/v1/health>
- the interactive API explorer at <http://localhost:8000/docs>

A full rebuild (`docker compose up --build`) is needed after any backend dependency change; code changes reload on their own. The demo world, and a ten-minute tour of it, are in document 10.

To start completely fresh, remove the containers **and the data volumes**: `docker compose down -v`. Without `-v` the database and uploaded files are kept.

Without a `GOOGLE_API_KEY` everything that does not call the model still works: accounts, jobs, applications, the pipeline, leave, document upload. What does not work is the AI itself: resume analysis, drafted emails, document embedding (and therefore Compass answers from documents), and the daily brief.

---

## 3. Every setting

All configuration is read in one place, `backend/app/core/config.py`, from environment variables or the `.env` file (names are case-insensitive). Nothing else in the backend reads the environment. A test (`test_docs_match_code`) fails if a setting exists in the code that this table does not mention.

### The settings that matter most

| Variable | Default | Meaning |
| --- | --- | --- |
| `ENVIRONMENT` | `local` | One of `local`, `test`, `staging`, `production`. Anything other than `local` and `test` triggers the startup checks described in section 4 |
| `DEBUG` | `true` | Development convenience. Must be `false` in `staging` and `production` |
| `GOOGLE_API_KEY` | empty | The key for Gemini, which powers every AI feature and document embedding. The only working provider |
| `JWT_SECRET_KEY` | `change-me-in-env` | The secret that signs sign-in tokens. In `staging` and `production` the application refuses to start if it is this default or shorter than 32 characters. Generate one with `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `DATABASE_URL` | `postgresql+asyncpg://talign:talign@localhost:5432/talign` | The database connection. Any common spelling is accepted, including the `postgres://…` form hosts hand out, and an `sslmode=` or `ssl=` option is translated for each driver. When `DATABASE_URL_SYNC` is not set it is derived from this one, so a deployment needs only this variable |
| `DATABASE_URL_SYNC` | `postgresql+psycopg2://talign:talign@localhost:5432/talign` | The same database for the migration tool (synchronous driver). Optional; normally derived from `DATABASE_URL` |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated list of the exact web addresses allowed to call the API from a browser (scheme, host, port, no trailing slash). `*` and entries without `http://` or `https://` are refused |
| `COOKIE_SAMESITE` | `lax` | How strictly browsers restrict the sign-in cookies: `lax`, `strict` or `none`. See section 5 for when `none` is needed. `none` needs HTTPS, so it is refused with `ENVIRONMENT=local` |

### All the rest

| Variable | Default | Meaning |
| --- | --- | --- |
| `APP_NAME` | `Talign` | The name shown in the API's documentation |
| `API_V1_PREFIX` | `/api/v1` | The URL prefix of every API route |
| `JWT_ALGORITHM` | `HS256` | The signing algorithm for tokens |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Lifetime of the short-lived access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `14` | Lifetime of the refresh cookie |
| `LOGIN_MAX_FAILED_ATTEMPTS` | `5` | Wrong passwords allowed for one (client address, email) pair before sign-in is refused |
| `LOGIN_LOCKOUT_WINDOW_SECONDS` | `900` | How long that refusal lasts, and the window in which failures are counted |
| `LLM_PROVIDER` | `gemini` | Accepts `gemini`, `openai` or `anthropic`, but **only `gemini` works**: the OpenAI class is an unfinished placeholder and `anthropic` is rejected. Despite what a comment in `.env.example` says, switching provider is not just a setting change |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` | empty | Reserved for providers that do not exist yet |
| `LLM_DEFAULT_MODEL` | `gemini-2.5-flash` | The chat model used by every agent |
| `STORAGE_PROVIDER` | `local` | Only `local` exists |
| `LOCAL_STORAGE_PATH` | `./storage` | Where uploaded resumes and knowledge documents are written |
| `MAX_RESUME_FILE_SIZE_BYTES` | `5242880` (5 MB) | Largest accepted resume |
| `MAX_KNOWLEDGE_FILE_SIZE_BYTES` | `20971520` (20 MB) | Largest accepted knowledge document |
| `ALLOWED_DOCUMENT_CONTENT_TYPES` | PDF, DOCX, plain text | Accepted upload types (a JSON list when set through the environment) |
| `KNOWLEDGE_RETRIEVAL_TOP_K` | `5` | How many document passages are retrieved for each question |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING` or `ERROR` |
| `LOG_JSON` | `false` | Structured JSON logs; intended for staging and production |

### Settings outside the backend's configuration class

| Variable | Where | Meaning |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | Frontend | The API's address as the browser sees it, e.g. `http://localhost:8000/api/v1`. **Next.js bakes this into the compiled code at build time**, so for a production build it must be set when the build runs, not only when the server starts |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | `docker-compose.yml` | Credentials of the bundled development database (all `talign`). Never reuse them anywhere real |
| `FORWARDED_ALLOW_IPS` | Uvicorn | Set to `*` when the API sits behind a proxy, so the login throttle sees real client addresses (see section 4) |

---

## 4. What is already hardened

These protections exist in the code today and were checked by tests (see document 08):

- **Unsafe configuration refuses to start.** With `ENVIRONMENT=staging` or `production`, the backend lists every problem (default or short secret, debug on) and exits, instead of running a deployed instance with development defaults.
- **Browser access is explicit.** CORS allows only the origins you list, and never `*`, because the API uses cookies.
- **Sign-in is throttled.** Five wrong passwords for one (client address, email) pair within fifteen minutes lock that pair out, even for the right password, with a `429` and a `Retry-After` header. The key is the pair rather than the address alone so that a misconfigured proxy cannot lock the whole site out.
- **Tokens are handled defensively.** The access token lives only in browser memory; the refresh token is an `httpOnly` cookie limited to one path; the server re-reads the user from the database on every request, so disabling an account takes effect immediately.
- **Crashes still reach the browser as readable errors.** An unexpected error returns a JSON `500` that still carries CORS headers, so the failure is not disguised as a CORS problem.
- **Company data is isolated** at the query level, and cross-company access answers `404`.

---

## 5. Production readiness: what is ready, what is verified, what remains

This section is deliberately specific about evidence. "Verified here" means it was run in the development sandbox, not on Render.

| Concern | Status | Evidence |
| --- | --- | --- |
| Development images in production | **Fixed.** The API has `backend/Dockerfile.prod`: no auto-reload, no development dependencies, listens on `$PORT`, applies migrations before starting. The web app needs no image: it is a static build | The production start command was run against an empty database: all 10 migrations applied, health green, a registration worked, and a second start applied nothing. A test checks the Dockerfile (migrate before serve, no reload) |
| The web app sleeping | **Avoided by design.** A static site is served by a CDN and never sleeps; only the API can | A real browser drove the static export behind a server that mimics Render's static hosting (see below) |
| Cookies and CORS across two addresses | **Avoided by design.** The host forwards `/api/*`, so the browser only ever uses one address; the sign-in cookie belongs to the site itself | The same browser run: sign in, reload on a candidate's page, sign out, all through the forwarding |
| Expired access token | **Fixed.** The API client renews it once and retries | 9 unit tests, including that writes are never repeated; mutation-checked |
| Sleeping API | **Handled.** A branded "waking up" screen; a signed-in visitor is not logged out; the page recovers by itself | Browser run: sign in, API switched off, reload (screen appears, still signed in), API switched on (page loads by itself) |
| Migrations by hand | **Fixed.** Run at container start | As above |
| Connection string from the host | **Fixed.** `postgres://…` is accepted and both driver forms are derived | 12 unit tests, and real bugs found and fixed on the way (see section 8) |
| Uploaded files on a wiped disk | **Mitigated, not fixed** | Resume files are never read back (their text is extracted at upload). Only re-indexing a document reads its file, and it now fails with a clear message and leaves the search index untouched. Persistent storage is still not implemented |
| Background work in the web process | Unchanged | An in-flight analysis can be lost on restart; the user re-runs it |
| The login throttle in memory | Unchanged | Correct for one instance |
| Password reset, invitations by email | Not built | There is no mail integration |

**What was not verified.** Anything that needs Render itself: that Render's static-site forwarding passes the sign-in cookie back and forth unchanged (the documentation and a sample project say it forwards requests, but this was not tested), what it answers while the API is still asleep (the waking screen treats any timeout or gateway error as "still waking", so the design does not depend on the answer), the real wake-up time, Render's build, and the first run of the GitHub Actions workflow.

---

## 6. Deploying to Render's free tier

### What Render's free tier is, as documented

Checked against Render's own documentation on the date this was written; **confirm these on the day**, because they change:

- A **free web service** spins down after 15 minutes without incoming traffic and takes about a minute to start again; browsers are shown Render's own loading page meanwhile. It has 512 MB of memory and a small share of a CPU. The Talign API used about 135 MB when idle in the development sandbox (with a stand-in for the AI, so the real AI libraries add some).
- Free instance hours are **750 a month, shared** across free web services. A service kept awake all month would use about 744 of them, which is why **keeping the API awake with pings is not recommended** (and one awake API leaves no hours for a second).
- A free web service has **no persistent disk**: its files are lost on every restart, spin-down or deploy.
- A **static site** is free, served from a CDN, does not spin down, and can rewrite a path to a full URL (used here to forward `/api/*` to the API).
- A **free Render Postgres database expires 30 days after creation** (with a 14-day grace period) and has no backups. It supports the `pgvector` extension that the Knowledge Center needs. The demo world is rebuildable with one command, so an expiry costs only what visitors added; a new database and a re-seed restore everything.
- Render states that free instances are not meant for production use. For a portfolio demo that is fine, and the README says so.

### The shape of the deployment

`render.yaml` at the repository root describes two services. **`talign`** is the static site: it builds the web app with `npm ci && npm run build` and publishes `frontend/out`. It carries the rewrite rules: `/api/*` is forwarded to the API, and the five dynamic page types are served from their placeholder files (the same rules as `frontend/static-host-rules.json`, which a backend test keeps in step). **`talign-api`** is a Docker web service built from `backend/Dockerfile.prod`, with `ENVIRONMENT=production`, `DEBUG=false`, a generated `JWT_SECRET_KEY`, and prompts for the two secrets it cannot know. The database is not in the file because it already exists.

### Steps

1. **Prepare.** Push the repository to GitHub. Restore `.github/workflows/ci.yml` if your working folder lost it, and wait for the first CI run to go green. Create a Gemini key in a Google project with **no billing attached**, so anyone using the public demo can only exhaust a free quota and never cost you money. Note your Render database's **region**, its **expiry date**, and its **Internal Database URL** (it starts with `postgres://` and has a short host like `dpg-…-a`).
2. **Create the services.** In the Render dashboard choose *New → Blueprint*, select the repository, and Render reads `render.yaml`. When it asks, paste the internal database URL as `DATABASE_URL` and the key as `GOOGLE_API_KEY`. If your database is not in the Oregon region, change `region:` in `render.yaml` first: the API and the database must share a region to use the private network.
3. **Fix the two addresses.** After the first deploy, Render shows the real address of each service. If the API's is not `talign-api.onrender.com`, put the real one in the `/api/*` rule in `render.yaml`; and if the site's is not `talign.onrender.com`, put it in `CORS_ORIGINS`. Commit and push; both services redeploy.
4. **Wake it and look.** Open `https://<your-site>/api/v1/health` (the first request after idle takes up to a minute). You should see `{"status":"ok","database":"ok"}`. Then open the site itself.
5. **Load the demo world** (optional but recommended for a portfolio link) from your own computer, which calls the live API:

   ```powershell
   pip install httpx
   python backend\scripts\seed_demo.py --api https://<your-site>/api/v1 --timeout 300
   ```

   The AI work (resume analysis, embeddings) runs on the API with the key you configured there, and the free instance is slow, so allow several minutes. The script is safe to re-run. The accounts and their shared password are in document 10: **publish them only if you want strangers to sign in**.
6. **Run the live checks** below.
7. **Optional: retake the README screenshots with real AI.** On your computer, with Node and Chrome installed:

   ```powershell
   cd tools\screenshots
   npm install
   $env:CHROME_PATH = "C:\Program Files\Google\Chrome\Application\chrome.exe"
   $env:TALIGN_URL = "https://<your-site>"
   node scenarios.mjs public apply candidate recruiter knowledge isolation failures
   ```

   Do **not** run the `hire` and `leave` groups against the live demo: they change its data.

### Live checks

These are the things only a real Render deployment can show. Each has a clear pass or fail:

1. **Sign-in survives a reload.** Sign in, open a candidate, press reload. You should stay signed in on the same page. If you are sent to the login page, the forwarding is not passing the sign-in cookie: in the browser's developer tools (Application, Cookies) there should be a `talign_refresh_token` cookie for the site's own address.
2. **Deep links work.** Paste a candidate's address into a new tab. It should open that candidate.
3. **The waking screen appears and goes away.** Leave the site idle for 20 minutes, then open it. The page should load at once, show "Waking up the server…", then continue on its own, still signed in.
4. **An upload and a Compass answer work** with the real key.
5. **The size of an upload passes the forwarding.** Upload a resume close to the 5 MB limit.
6. **Free-hour budget.** After a few days, check Render's dashboard: the API should be using far fewer than 750 hours.

### If the forwarding does not behave

If check 1 fails, the cause is Render's forwarding, not the application. The fallbacks, in order of effort: serve the web app from a Node web service instead of a static site (it forwards `/api` itself, at the cost of a second service that sleeps, with its own waking page); or serve the API and the web app from two addresses with cross-site cookies (`COOKIE_SAMESITE=none`, needs HTTPS, and browsers that block third-party cookies would break it). Neither is built; the first is the more reliable and would be the next piece of work.

### Trying the production build on your own computer

You can run exactly what Render will serve, without Render. With the API running on port 8000:

```powershell
cd frontend
$env:NEXT_PUBLIC_API_URL = "/api/v1"
npm run build            # needs internet once, to fetch the Inter typeface
npm run serve:export     # serves frontend/out on http://localhost:3000 and forwards /api to :8000
```

`npm run serve:export` applies the same rewrite rules as `render.yaml` and answers `502` when the API is down, like a gateway would.

### Keeping the demo healthy

The database expires 30 days after it was created. Put the expiry date in your calendar: before it, create a new free database, set the new internal URL as `DATABASE_URL`, let the API redeploy (it migrates on start), and run the seed again. Uploaded files vanish whenever the API restarts; only document re-indexing needs them.

---

## 7. Troubleshooting

| Symptom | Likely cause and fix |
| --- | --- |
| The browser reports a CORS error | First check the API's logs for a crash: a `500` used to be disguised as a CORS error. With the forwarding in place the browser should not make cross-origin calls at all, so a CORS error usually means the page is calling the API's own address directly: check `NEXT_PUBLIC_API_URL` was `/api/v1` **when the site was built** (it is baked in at build time) |
| The API will not start and lists problems | `ENVIRONMENT` is `staging` or `production` with the default secret, a short secret, or `DEBUG=true`. Fix the listed settings |
| The API starts, then every request fails with a database error | `DATABASE_URL` is wrong, or the API and the database are in different regions and the internal address does not resolve. Check the region and that you used the *internal* URL |
| Migrations fail on a fresh database | The database user cannot create the `vector` extension, or the database is below PostgreSQL 13 |
| The site loads but every API call returns `502` for more than two minutes | The API failed to start. Read its logs in the Render dashboard |
| The waking screen never goes away | The API cannot start (see above), or the forwarding destination in `render.yaml` is not the API's real address |
| Sign-in works, but a reload logs you out | The forwarding is not passing the cookie (live check 1) |
| Container name or port conflicts on `docker compose up` | An old stack is still present. Run `docker compose down`, and if needed `docker rm -f talign-postgres talign-backend talign-frontend` |
| Every AI feature returns a `502` | `GOOGLE_API_KEY` is missing, wrong, over its free quota, or the provider is unreachable. Non-AI features are unaffected |
| An uploaded resume is marked as unreadable | It has no extractable text, typically a scan. Upload a text-based PDF, DOCX or TXT file |
| Re-indexing a document says its file is no longer stored | The API restarted and its disk was reset (free tier). The existing search index is unchanged and still works; upload the file again to replace it |
| A document is stuck before `ready` after a restart | The in-process embedding task was interrupted. Re-index it from the Knowledge Center |
| Locked out after several wrong passwords | The throttle holds for 15 minutes for that address and email, even for the right password. Wait, or restart the API (the state is in memory) |

---

## 8. Things found by actually running it

Writing this section of the work turned up four problems that reading the code and running the existing tests had not, which is the argument for running the real thing:

1. **The development server broke on every candidate, job and application page** once the static export was configured, because Next.js refuses on-demand ids in export mode. The export is therefore enabled for production builds only.
2. **Migrations crashed on a connection string with a percent-encoded character** (a password containing `@` is written `%40`), because Alembic's configuration reader treats `%` as special. This was a latent bug for any such URL, not only the host's form; fixed in `alembic/env.py`.
3. **My own first URL translation re-encoded a socket path** in the query string and triggered the same crash; the translation now leaves untouched parts exactly as given.
4. **Re-indexing deleted a document's search index before reading its file**, so a missing file relied on a rollback to protect it. It now reads the file first.
