# Screenshot tooling

This folder produced every image in `docs/assets/screenshots/`. It is development tooling, not part of the product, and it exists so the pictures in the README can be retaken after the interface changes, instead of going stale.

## What the screenshots are, and are not

They are **real screenshots of the real application** running against a real PostgreSQL database loaded with the seeded demo world (`backend/scripts/seed_demo.py`), driven by a headless browser that signs in through the actual login form and clicks the actual buttons.

They were taken **without a Gemini API key**, using a **demo stand-in** for the AI (`demo_ai.py`). The stand-in is a small rule-based program, not a language model. It reads the real resume text and judges each required skill against it, answers policy questions from the passages that were retrieved, and fills emails and the daily brief from templates. That makes every screen structurally realistic, with a believable spread of scores, but **the wording and the exact scores are not what Gemini would produce**, and nothing here measures AI quality. Retake the images with a real key to show real model output (see below).

## Files

| File | Purpose |
| --- | --- |
| `demo_ai.py` | The demo AI stand-in (resume extraction and judgement, grounded policy answers, emails, brief, Compass explanations, and a retrieval stand-in for embeddings) |
| `demo_launcher.py` | Starts the real backend with the stand-in in place of Gemini |
| `lib.mjs` | Browser launch, bundled Inter font, UI-driven sign-in, wait-for-content and screenshot helpers |
| `scenarios.mjs` | The scenarios, as groups: `public apply candidate recruiter knowledge hire leave isolation failures` |

## Retaking them (with the demo stand-in)

You need a running database with migrations applied and the demo world seeded, the backend started through `demo_launcher.py`, and the frontend running on port 3000. After starting the backend, re-index each company's documents (the stand-in's retrieval index lives in memory), then run the groups.

```bash
cd tools/screenshots
npm install
node scenarios.mjs public apply candidate recruiter knowledge isolation failures   # read-only groups
node scenarios.mjs hire leave                                                       # these CHANGE the data
```

The `hire` group hires Wei Zhang and the `leave` group approves Sarah Lopez's pending request, so run them once per freshly seeded database (reset with `docker compose down -v` and seed again).

On a machine with Chrome or Chromium installed, set `CHROME_PATH` to its executable and the bundled Linux Chromium (`@sparticuz/chromium`) is not used. `TALIGN_URL` overrides the default `http://localhost:3000`.

## Retaking them with real AI

Skip `demo_launcher.py`: start the normal stack with a real `GOOGLE_API_KEY`, seed it, and run the same scenarios. Expect different scores and wording, and check the screens that quote them. Two details of the scripts assume the demo data and should be reviewed if you change the seed: the candidate names used to open workspaces, and the questions asked in the knowledge group.

## Fonts

The application loads the Inter typeface from Google Fonts at build time. Where that is unreachable it falls back to a system font, so `lib.mjs` injects Inter from the `@fontsource/inter` package into every page. This changes nothing but the typeface.
