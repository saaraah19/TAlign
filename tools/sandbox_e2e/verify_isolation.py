"""
Checks over real HTTP, against a backend seeded by backend/scripts/seed_demo.py:
tenant isolation (each company sees only its own data), role permissions, the
public job board, the leave balance, the dashboard and Compass. Usage:
    python tools/sandbox_e2e/verify_isolation.py
(The two Compass-citation checks need working embeddings: with the sandbox
stand-ins in launcher.py they only prove the wiring.)
"""

import sys

import httpx

B = "http://127.0.0.1:8000/api/v1"
PW = "Demo!Pass123"
c = httpx.Client(base_url=B, timeout=30)
fails = 0


def check(name, cond, extra=""):
    global fails
    if not cond:
        fails += 1
        print("FAIL", name, extra)
    else:
        print("ok  ", name)


tok = {}


def get(email, path, **kw):
    if email not in tok:
        r = c.post("/auth/login", json={"email": email, "password": PW})
        assert r.status_code == 200, (email, r.text)
        tok[email] = r.json()["access_token"]
    return c.get(path, headers={"Authorization": f"Bearer {tok[email]}"}, **kw)


def post(email, path, body):
    if email not in tok:
        get(email, "/auth/me")
    return c.post(path, headers={"Authorization": f"Bearer {tok[email]}"}, json=body)


OLIVIA, EMMA, DAVID = (
    "olivia.brown@northwind-robotics.com",
    "emma.martin@northwind-robotics.com",
    "david.chen@northwind-robotics.com",
)
GRACE, LIAM, NOAH = (
    "grace.okafor@helix-health.io",
    "liam.becker@helix-health.io",
    "noah.fischer@brightpath-logistics.com",
)
SARAH, ALEX = "sarah.lopez@candidates-demo.com", "alex.johnson@candidates-demo.com"

titles = lambda r: sorted(i["title"] for i in r.json()["items"])
# --- companies see only their own data
check(
    "Northwind admin sees 6 documents",
    len(get(OLIVIA, "/knowledge/documents").json()["items"]) == 6,
)
check(
    "Helix admin sees only Helix's 2 documents",
    titles(get(GRACE, "/knowledge/documents")) == ["Leave Policy", "Patient Data Privacy Handbook"],
)
check(
    "Northwind sees 6 jobs; Helix sees its 2; Brightpath sees none",
    len(get(EMMA, "/jobs", params={"page_size": 100}).json()["items"]) == 6
    and titles(get(LIAM, "/jobs")) == ["Clinical Product Manager", "Healthcare Data Analyst"]
    and get(NOAH, "/jobs").json()["total"] == 0,
)
nw_apps = get(EMMA, "/applications", params={"page_size": 100}).json()
check(
    "Emma's pipeline has the 18 Northwind applications",
    nw_apps["total"] == 18,
    str(nw_apps["total"]),
)
hx_apps = get(LIAM, "/applications", params={"page_size": 100}).json()
check(
    "Liam's pipeline has only Helix's 2 applications", hx_apps["total"] == 2, str(hx_apps["total"])
)
a_northwind = nw_apps["items"][0]["id"]
check(
    "another company cannot open a Northwind application by its id (404, not 403)",
    get(LIAM, f"/applications/{a_northwind}").status_code == 404,
)
check("a brand-new company's pipeline is empty", get(NOAH, "/applications").json()["total"] == 0)
# --- public job board
pub = c.get("/public/jobs", params={"page_size": 100}).json()
check(
    "public board lists exactly the 6 OPEN jobs (draft and closed hidden)",
    pub["total"] == 6,
    str(pub["total"]),
)
names = {i["title"]: i["company_name"] for i in pub["items"]}
check(
    "each public job carries its own employer's name",
    names.get("Backend Engineer") == "Northwind Robotics"
    and names.get("Healthcare Data Analyst") == "Helix Health",
)
check(
    "draft and closed jobs are not public",
    "Product Designer" not in names and "Customer Success Manager" not in names,
)
# --- roles and permissions
check(
    "a hired employee (Sarah) can read the Knowledge Center",
    get(SARAH, "/knowledge/documents").status_code == 200,
)
check("...but is refused the jobs list (403)", get(SARAH, "/jobs").status_code == 403)
check(
    "a candidate (Alex) is refused staff endpoints (403)",
    get(ALEX, "/jobs").status_code == 403 and get(ALEX, "/knowledge/documents").status_code == 403,
)
check(
    "the recruiter cannot approve leave (admin/hiring manager only)",
    get(EMMA, "/leave-requests").status_code == 403,
)
check(
    "the hiring manager can see the leave queue", get(DAVID, "/leave-requests").status_code == 200
)
q = get(DAVID, "/leave-requests", params={"status": "pending"}).json()
check(
    "exactly one leave request is still pending (the vacation)",
    q["total"] == 1 and q["items"][0]["leave_type"] == "vacation",
)
# --- leave balance reflects the approved sick leave (2 calendar days)
bal = get(SARAH, "/leave-requests/mine/balance").json()
check(
    "Sarah's balance: 2 of 20 days used, 18 remaining",
    bal["days_used"] == 2 and bal["days_remaining"] == 18 and bal["annual_allotment"] == 20,
    str(bal),
)
# --- dashboard
dash = get(EMMA, "/dashboard")
check("the recruiter dashboard loads", dash.status_code == 200, dash.text[:150])
# --- Compass, for an employee and for a candidate on their own application
ans = post(SARAH, "/compass/ask", {"message": "How many leave days do I get?"})
if ans.status_code == 502 and "sandbox stand-in" in ans.text:
    # The stand-in "LLM" cannot produce the document ids a cited answer needs.
    # That limits this tool, not the app; run against real Gemini to check these.
    print("skip Compass policy answer + citations (the sandbox AI cannot cite; needs real Gemini)")
else:
    check(
        "Compass answers an employee's policy question",
        ans.status_code == 200 and len(ans.json().get("message", "")) > 5,
        ans.text[:150],
    )
    check(
        "...and cites the company's own documents",
        bool(ans.json().get("citations")),
        ans.text[:200],
    )
    cites = {x["document_title"] for x in (ans.json().get("citations") or [])}
    check(
        "...only from Northwind's documents (never Helix's)",
        "Patient Data Privacy Handbook" not in cites,
        str(cites),
    )
mine = get(ALEX, "/applications/mine").json()["items"][0]["id"]
r = post(
    ALEX, "/compass/ask", {"message": "What stage is my application at?", "application_id": mine}
)
check(
    "Compass tells a candidate their application status",
    r.status_code == 200 and "interview" in r.json()["message"].lower(),
    r.text[:200],
)
print("\nALL ISOLATION CHECKS PASSED" if not fails else f"\n{fails} FAILURE(S)")
sys.exit(1 if fails else 0)
