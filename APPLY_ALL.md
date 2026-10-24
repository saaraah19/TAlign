# Talign - complete update (replaces batches 1-6)

This ONE zip contains the final version of every file that changed (93 files). It works
whatever you applied before. Do NOT apply the older batch zips; ignore them.
It was tested on a fresh copy of your original upload: backend 373 tests, frontend 162 tests,
type-check and lint clean, production build 22/22 pages.

## 1. Copy the files
Unzip over the repo root and choose "replace all". Make sure the files in the bracket
folders landed INSIDE them, e.g.
  frontend\src\app\(protected)\pipeline\[id]\page.tsx   and   ...\[id]\client.tsx

## 2. Delete / move (PowerShell, from the repo root)
  Remove-Item frontend\src\middleware.ts
  New-Item -ItemType Directory -Force docs\history | Out-Null
  Move-Item docs\00_slice0_foundation.md          docs\history\
  Move-Item docs\01_slice1_authentication.md      docs\history\
  Move-Item docs\02_slice2_jobs.md                docs\history\
  Move-Item docs\03_slice3_applications.md        docs\history\
  Move-Item docs\04_slice4_resume_intelligence.md docs\history\
  Move-Item HANDOVER.md                           docs\history\
  Move-Item HANDOVER_redesign_through_phase3.md   docs\history\
  Move-Item HANDOVER_redesign_through_phase6.md   docs\history\
  Remove-Item PROJECT_STATUS.md, DEMO_WALKTHROUGH.md
(Leave HANDOVER_polish_hardening_seed.md where it is for now.)

## 3. Git housekeeping
  git restore .github            # your folder is missing .github\workflows\ci.yml
  git add --renormalize .        # once: clears the phantom Windows line-ending changes
  git status                     # look it over before committing

## 4. Rebuild and look (backend code changed)
  docker compose up --build
Open http://localhost:3000 and sign in as before. Nothing else is needed: no new
dependencies, no new database migration.

## 5. Check (optional but recommended)
  cd frontend ; npm run typecheck ; npm run lint ; npm test     # 162 tests
  cd ..\backend ; pytest                                          # 373 tests

## 6. Push, then tell me what GitHub Actions says
  git add -A ; git commit -m "Documentation, static-site deployment, audit" ; git push
The first CI run on GitHub has never happened yet; it may show something my machine did not.

## 7. Going online
Follow docs/09_deployment.md, section 6. You will need: a Render account connected to
your GitHub repo, your existing Render database's internal URL, region and expiry date,
and a Gemini key from a Google project with NO billing attached.
