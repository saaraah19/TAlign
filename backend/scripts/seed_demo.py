#!/usr/bin/env python3
"""
Fill a running Talign backend with a realistic demo world, so the whole
workflow can be tried without typing a single form.

    # backend + database already running (docker compose up):
    docker compose exec backend python scripts/seed_demo.py

    # or from your own machine, against a backend on localhost:
    python backend/scripts/seed_demo.py --api http://localhost:8000/api/v1

What it creates: three fictional companies with their staff, company
documents for the Knowledge Center, job postings, sixteen candidates with
real resume files, their applications, and what recruiters then do with
them (screening, interviews, an offer, a rejection, a hire, drafted emails)
plus leave requests for the employee who was hired. See
backend/seed_data/demo_data.py for exactly who and what.

HOW IT WORKS, AND WHY: it plays everything through the same public HTTP API
the website uses (register, log in, post a job, apply, upload a resume...),
never by writing to the database directly. That makes it a smoke test of the
real product (validation, permissions, background AI analysis, the hire
workflow all run for real), and it keeps working when the database schema
changes.

SAFE TO RE-RUN: every step first checks whether its work already exists, so
a second run adds nothing twice. To start over from nothing, wipe the
database (`docker compose down -v`) and bring it up again.

THE AI PARTS NEED A WORKING GOOGLE_API_KEY in the backend's .env: resume
analysis, drafted emails and document embeddings call Gemini. Without it
the script still creates everything and tells you which AI steps failed; the
accounts, jobs, applications and pipeline are real either way.
"""

import argparse
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import httpx

SEED_DATA = Path(__file__).resolve().parent.parent / "seed_data"
sys.path.insert(0, str(SEED_DATA))

import demo_data as data

CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
}
STAGE_ORDER = ["applied", "screening", "interview", "offer", "hired"]
JOB_ORDER = ["draft", "open", "closed"]


class SeedError(Exception):
    """Something the script cannot continue past."""


def say(message: str, depth: int = 0) -> None:
    print("  " * depth + message, flush=True)


class Api:
    """A thin client: remembers each user's token and signs back in if it expires."""

    def __init__(self, base_url: str) -> None:
        self.client = httpx.Client(base_url=base_url.rstrip("/"), timeout=120)
        self.tokens: dict[str, str] = {}

    def login(self, email: str) -> None:
        r = self.client.post("/auth/login", json={"email": email, "password": data.DEMO_PASSWORD})
        if r.status_code == 429:
            raise SeedError(f"Login for {email} is temporarily locked (too many failed attempts): {r.json()['detail']}")
        if r.status_code != 200:
            raise SeedError(
                f"Could not sign in as {email} (HTTP {r.status_code}). If this account already exists "
                f"from an earlier, different seed, wipe the database (docker compose down -v) and retry."
            )
        self.tokens[email] = r.json()["access_token"]

    def request(self, method: str, path: str, *, as_user: str | None = None,
                allow: tuple[int, ...] = (200, 201, 202, 204), **kwargs) -> httpx.Response:
        headers = {}
        if as_user:
            if as_user not in self.tokens:
                self.login(as_user)
            headers["Authorization"] = f"Bearer {self.tokens[as_user]}"
        r = self.client.request(method, path, headers=headers, **kwargs)
        if r.status_code == 401 and as_user:  # access token expired mid-run: sign in again, once
            self.login(as_user)
            headers["Authorization"] = f"Bearer {self.tokens[as_user]}"
            r = self.client.request(method, path, headers=headers, **kwargs)
        if r.status_code not in allow:
            raise SeedError(f"{method} {path} as {as_user or 'anonymous'} -> HTTP {r.status_code}: {r.text[:300]}")
        return r

    def get(self, path: str, as_user: str, **kwargs) -> httpx.Response:
        return self.request("GET", path, as_user=as_user, **kwargs)


# --------------------------------------------------------------------- steps
def ensure_company(api: Api, company: dict) -> None:
    admin = company["admin"]
    r = api.request(
        "POST", "/auth/register/company", allow=(201, 409),
        json={"company_name": company["name"], "admin_first_name": admin["first"],
              "admin_last_name": admin["last"], "email": admin["email"], "password": data.DEMO_PASSWORD},
    )
    if r.status_code == 201:
        api.tokens[admin["email"]] = r.json()["access_token"]
        say(f"+ company {company['name']} (admin {admin['email']})", 1)
    else:
        api.login(admin["email"])
        say(f"= company {company['name']} already exists", 1)

    for person in company["staff"]:
        r = api.request(
            "POST", "/auth/internal-users", as_user=admin["email"], allow=(201, 409),
            json={"email": person["email"], "first_name": person["first"], "last_name": person["last"],
                  "role": person["role"], "password": data.DEMO_PASSWORD},
        )
        say(f"{'+' if r.status_code == 201 else '='} {person['role']}: {person['first']} {person['last']} ({person['email']})", 2)


def upload_knowledge(api: Api, company: dict) -> list[str]:
    admin = company["admin"]["email"]
    if not company["knowledge"]:
        return []
    existing = {d["title"] for d in api.get("/knowledge/documents", admin, params={"page_size": 100}).json()["items"]}
    uploaded = []
    for doc in company["knowledge"]:
        if doc["title"] in existing:
            say(f"= document {doc['title']!r} already uploaded", 2)
            continue
        path = SEED_DATA / "knowledge" / doc["file"]
        api.request(
            "POST", "/knowledge/documents", as_user=admin, allow=(201,),
            data={"title": doc["title"], "category": doc["category"]},
            files={"file": (path.name, path.read_bytes(), CONTENT_TYPES[path.suffix])},
        )
        uploaded.append(doc["title"])
        say(f"+ document {doc['title']!r} ({doc['category']})", 2)
    return uploaded


def wait_for_documents(api: Api, company: dict, timeout: int) -> None:
    admin = company["admin"]["email"]
    deadline = time.time() + timeout
    while time.time() < deadline:
        docs = api.get("/knowledge/documents", admin, params={"page_size": 100}).json()["items"]
        pending = [d for d in docs if d["status"] not in ("ready", "failed")]
        if not pending:
            failed = [d["title"] for d in docs if d["status"] == "failed"]
            if failed:
                say(f"! these documents could not be processed (is GOOGLE_API_KEY set?): {', '.join(failed)}", 2)
            else:
                say(f"✓ all {len(docs)} documents are ready for Compass", 2)
            return
        time.sleep(2)
    say("! still processing documents after the timeout; they will finish in the background", 2)


def ensure_jobs(api: Api, company: dict) -> dict[str, str]:
    """Create the company's jobs and bring each to its final status. Returns job key -> id."""
    admin = company["admin"]["email"]
    author = next((p["email"] for p in company["staff"] if p["role"] == "recruiter"), admin)
    existing = {j["title"]: j for j in api.get("/jobs", admin, params={"page_size": 100}).json()["items"]}
    ids: dict[str, str] = {}
    for job in company["jobs"]:
        found = existing.get(job["title"])
        if found:
            job_id, status = found["id"], found["status"]
        else:
            body = {k: job[k] for k in ("title", "description", "employment_type", "location", "salary_min",
                                        "salary_max", "salary_currency", "required_skills", "preferred_skills",
                                        "min_years_experience")}
            created = api.request("POST", "/jobs", as_user=author, allow=(201,), json=body).json()
            job_id, status = created["id"], created["status"]
        # Walk the job forward (draft -> open -> closed) until it reaches its final status.
        for step in JOB_ORDER[JOB_ORDER.index(status) + 1 : JOB_ORDER.index(job["final_status"]) + 1]:
            api.request("POST", f"/jobs/{job_id}/transition", as_user=author, json={"target_status": step})
            status = step
        ids[job["key"]] = job_id
        say(f"{'=' if found else '+'} job {job['title']!r}: {status}", 2)
    return ids


def ensure_candidate(api: Api, person: dict) -> dict[str, str] | None:
    """Register (or sign in) a candidate and upload their resumes.

    Returns None when the account is no longer a candidate: someone who was
    hired in an earlier run is now an employee, and the candidate-only
    endpoints correctly answer 403. A re-run must simply leave them alone.
    """
    email = person["email"]
    r = api.request("POST", "/auth/register/candidate", allow=(201, 409),
                    json={"first_name": person["first"], "last_name": person["last"],
                          "email": email, "password": data.DEMO_PASSWORD})
    if r.status_code == 201:
        api.tokens[email] = r.json()["access_token"]
    else:
        api.login(email)

    listing = api.request("GET", "/resumes/mine", as_user=email, allow=(200, 403))
    if listing.status_code == 403:
        return None
    have = {x["original_filename"]: x["id"] for x in listing.json()}
    resume_ids: dict[str, str] = {}
    for filename in [person["resume"], *person.get("extra_resumes", [])]:
        if filename in have:
            resume_ids[filename] = have[filename]
            continue
        path = SEED_DATA / "resumes" / filename
        # A resume that cannot be read is stored anyway (marked unreadable): that is the point of the demo file.
        r = api.request("POST", "/resumes", as_user=email, allow=(201, 422, 400),
                        files={"file": (path.name, path.read_bytes(), CONTENT_TYPES[path.suffix])})
        if r.status_code == 201:
            resume_ids[filename] = r.json()["id"]
        else:
            say(f"! {filename} was refused ({r.json().get('detail', r.status_code)}); continuing", 3)
    return resume_ids


def find_application_as_staff(api: Api, company_key: str, job_id: str, candidate_email: str) -> str | None:
    """Look an application up the way the company's recruiter would (by the candidate's email)."""
    recruiter = data.RECRUITER_FOR[company_key]
    items = api.get("/applications", recruiter, params={"job_id": job_id, "page_size": 100}).json()["items"]
    return next((i["id"] for i in items if i["candidate"]["email"] == candidate_email), None)


def wait_for_analysis(api: Api, candidate: str, application_id: str, timeout: int) -> str:
    deadline = time.time() + timeout
    status = "unknown"
    while time.time() < deadline:
        status = api.get(f"/applications/mine/{application_id}/analysis-status", candidate).json()["status"]
        if status in ("complete", "failed"):
            return status
        time.sleep(2)
    return status


def apply_all(api: Api, jobs: dict[tuple[str, str], str], wait: bool, timeout: int, pace: float) -> dict:
    """Candidates register, upload resumes and apply. Returns (company, job, email) -> application id."""
    applications: dict[tuple[str, str, str], str] = {}
    for person in data.CANDIDATES:
        email = person["email"]
        say(f"{person['first']} {person['last']} <{email}>", 1)
        resume_ids = ensure_candidate(api, person)
        if resume_ids is None:
            say("= already hired: now an employee, so nothing is left to do as a candidate", 2)
            for company_key, job_key in person["applications"]:
                found = find_application_as_staff(api, company_key, jobs[(company_key, job_key)], email)
                if found:
                    applications[(company_key, job_key, email)] = found
            continue
        resume_id = resume_ids.get(person["resume"])
        if not resume_id:
            say("! no usable resume; skipping applications", 2)
            continue
        mine = {a["job"]["id"]: a["id"] for a in api.get("/applications/mine", email, params={"page_size": 100}).json()["items"]}
        for company_key, job_key in person["applications"]:
            job_id = jobs[(company_key, job_key)]
            title = next(j["title"] for c in data.COMPANIES if c["key"] == company_key for j in c["jobs"] if j["key"] == job_key)
            if job_id in mine:
                application_id, fresh = mine[job_id], False
            else:
                application_id = api.request("POST", "/applications", as_user=email, allow=(201,),
                                             json={"job_id": job_id}).json()["id"]
                fresh = True
            applications[(company_key, job_key, email)] = application_id

            state = api.get(f"/applications/mine/{application_id}/analysis-status", email).json()["status"]
            if state == "not_started":
                api.request("PUT", f"/applications/mine/{application_id}/resume", as_user=email,
                            json={"resume_id": resume_id})
                outcome = ""
                if wait:
                    outcome = f" -> analysis {wait_for_analysis(api, email, application_id, timeout)}"
                else:
                    time.sleep(pace)
                say(f"+ applied to {title!r} with {person['resume']}{outcome}", 2)
            else:
                say(f"{'+' if fresh else '='} application to {title!r} (analysis: {state})", 2)
    return applications


def retry_failed_analyses(api: Api, applications: dict, timeout: int) -> None:
    """One more try for analyses that failed (typically a momentary AI rate limit)."""
    retried = 0
    for (company_key, _job, email), application_id in applications.items():
        recruiter = data.RECRUITER_FOR[company_key]
        if api.get(f"/applications/{application_id}/analysis-status", recruiter).json()["status"] == "failed":
            api.request("POST", f"/applications/{application_id}/reanalyze", as_user=recruiter)
            outcome = wait_for_analysis(api, email, application_id, timeout)
            say(f"retried {email}: {outcome}", 2)
            retried += 1
    if not retried:
        say("no analysis needed a retry", 2)


def run_pipeline(api: Api, applications: dict, wait: bool) -> None:
    for story in data.PIPELINE:
        recruiter = data.RECRUITER_FOR[story["company"]]
        key = (story["company"], story["job"], story["candidate"])
        application_id = applications.get(key)
        if not application_id:
            say(f"! no application for {story['candidate']}; skipping", 1)
            continue
        say(f"{story['candidate']}", 1)
        status = api.get(f"/applications/{application_id}", recruiter).json()["status"]
        # The app refuses to draft an email for a rejected application, so a
        # rejection email has to be written BEFORE the candidate is rejected.
        if story.get("draft") == "rejection":
            draft_email(api, recruiter, application_id, story)
        for target in story["moves"]:
            terminal = target == "rejected"
            if terminal and status in ("rejected", "hired"):
                continue
            if not terminal and STAGE_ORDER.index(target) <= STAGE_ORDER.index(status):
                continue
            api.request("POST", f"/applications/{application_id}/transition", as_user=recruiter,
                        json={"target_status": target})
            status = target
        say(f"now: {status}", 2)

        if status == "hired" and wait:
            for _ in range(30):
                run = api.get(f"/applications/{application_id}/hire-workflow", recruiter).json().get("workflow_run")
                if run:
                    say(f"hire workflow {run['status']}: employee record, onboarding checklist, welcome email, portal access", 2)
                    break
                time.sleep(2)

        if story.get("draft") and story["draft"] != "rejection":
            draft_email(api, recruiter, application_id, story)


def draft_email(api: Api, recruiter: str, application_id: str, story: dict) -> None:
    emails = api.get(f"/applications/{application_id}/emails", recruiter).json()["items"]
    existing = next((e for e in emails if e["email_type"] == story["draft"]), None)
    if existing is None:
        r = api.request("POST", f"/applications/{application_id}/emails/draft", as_user=recruiter,
                        allow=(200, 201, 400, 409, 422, 500, 502, 503), json={"email_type": story["draft"]})
        if r.status_code == 409:
            say(f"= no {story['draft'].replace('_', ' ')} email drafted: {r.json().get('detail')}", 2)
            return
        if r.status_code not in (200, 201):
            say(f"! could not draft the {story['draft'].replace('_', ' ')} email (is GOOGLE_API_KEY set?)", 2)
            return
        existing = r.json()
        say(f"+ drafted the {story['draft'].replace('_', ' ')} email", 2)
    if story.get("mark_sent") and existing["status"] == "draft":
        api.request("POST", f"/applications/{application_id}/emails/{existing['id']}/send", as_user=recruiter)
        say("+ marked it as sent (Talign records it; you send the real email yourself)", 2)


def run_leave(api: Api) -> None:
    plan = data.LEAVE
    employee = plan["employee"]
    try:
        api.login(employee)  # the account was converted by the hire workflow: same login, new role
        existing = api.get("/leave-requests/mine", employee, params={"page_size": 100}).json()["items"]
    except SeedError as err:
        say(f"! skipped leave requests: {err}", 1)
        return
    if existing:
        say(f"= {len(existing)} leave requests already exist", 1)
        return
    today = date.today()  # noqa: DTZ011  (the local calendar date is what a person means by "in 45 days")
    for item in plan["requests"]:
        start = today + timedelta(days=item["start_in_days"])
        end = start + timedelta(days=item["length_days"] - 1)
        created = api.request("POST", "/leave-requests", as_user=employee, allow=(201,), json={
            "start_date": start.isoformat(), "end_date": end.isoformat(),
            "leave_type": item["type"], "reason": item["reason"]}).json()
        if item["outcome"] in ("approve", "reject"):
            api.request("POST", f"/leave-requests/{created['id']}/{item['outcome']}", as_user=item["by"])
        say(f"+ {item['type']} leave {start} -> {end}: {item['outcome'].replace('approve', 'approved').replace('reject', 'rejected')}", 1)


def summary(api: Api, jobs: dict[tuple[str, str], str]) -> None:
    say("\n" + "=" * 72)
    say("DEMO ACCOUNTS  (every account uses the password below)")
    say("=" * 72)
    say(f"password: {data.DEMO_PASSWORD}\n")
    for c in data.COMPANIES:
        say(f"{c['name']}")
        say(f"  admin / HR director : {c['admin']['email']}")
        for p in c["staff"]:
            say(f"  {p['role']:<19} : {p['email']}")
    say("\nCandidates: <firstname>.<lastname>@candidates-demo.com  (e.g. alex.johnson@candidates-demo.com)")
    say("Employee   : sarah.lopez@candidates-demo.com  (she was hired, so she signs in as an employee now)")

    say("\nWHAT THE RECRUITERS SEE  (alignment score = AI analysis; '-' = not scored)")
    for company_key, recruiter in data.RECRUITER_FOR.items():
        for c in data.COMPANIES:
            if c["key"] != company_key:
                continue
            for job in c["jobs"]:
                job_id = jobs.get((company_key, job["key"]))
                if not job_id or job["final_status"] != "open":
                    continue
                items = api.get("/applications", recruiter, params={"job_id": job_id, "page_size": 100}).json()["items"]
                if not items:
                    continue
                say(f"\n  {c['name']} - {job['title']}")
                for item in sorted(items, key=lambda i: -(i["latest_score"] or -1)):
                    score = "-" if item["latest_score"] is None else f"{item['latest_score']:.0f}"
                    name = f"{item['candidate']['first_name']} {item['candidate']['last_name']}"
                    say(f"    {score:>4}  {name:<20} {item['status']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed a running Talign backend with demo data.")
    parser.add_argument("--api", default="http://localhost:8000/api/v1", help="API base URL (default: %(default)s)")
    parser.add_argument("--no-wait", action="store_true",
                        help="don't wait for the AI to finish each analysis (faster, scores appear later)")
    parser.add_argument("--timeout", type=int, default=120, help="seconds to wait for each AI step (default: %(default)s)")
    parser.add_argument("--pace", type=float, default=1.0, help="with --no-wait, seconds between applications")
    args = parser.parse_args()
    wait = not args.no_wait
    api = Api(args.api)

    try:
        health = api.client.get("/health")
        if health.status_code != 200:
            raise SeedError(f"The backend answered {health.status_code} at {args.api}/health")
    except httpx.TransportError as err:
        raise SeedError(f"Cannot reach the backend at {args.api}: {err}") from err

    say("1/5  Companies, staff and documents")
    uploaded: dict[str, list[str]] = {}
    for company in data.COMPANIES:
        ensure_company(api, company)
        uploaded[company["key"]] = upload_knowledge(api, company)
    if wait:
        for company in data.COMPANIES:
            if uploaded[company["key"]]:
                say(f"{company['name']}: waiting for documents to be processed...", 1)
                wait_for_documents(api, company, args.timeout)

    say("\n2/5  Jobs")
    jobs: dict[tuple[str, str], str] = {}
    for company in data.COMPANIES:
        say(company["name"], 1)
        for key, job_id in ensure_jobs(api, company).items():
            jobs[(company["key"], key)] = job_id

    say("\n3/5  Candidates apply (each resume is read and scored by the AI)")
    applications = apply_all(api, jobs, wait, args.timeout, args.pace)
    if wait:
        say("\n     Retrying any analysis that failed:", 1)
        retry_failed_analyses(api, applications, args.timeout)

    say("\n4/5  Recruiters work the pipeline")
    run_pipeline(api, applications, wait)

    say("\n5/5  The new employee requests leave")
    run_leave(api)

    summary(api, jobs)
    say("\nDone. Open http://localhost:3000 and sign in with any account above.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SeedError as error:
        print(f"\nSeed stopped: {error}", file=sys.stderr)
        sys.exit(1)
