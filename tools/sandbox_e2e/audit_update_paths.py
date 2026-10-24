"""
Exercises EVERY data-changing endpoint against a running, seeded backend and fails if any answers 5xx.

Why this exists: the application uses async SQLAlchemy, which cannot fetch missing data on demand
and which discards some columns (every model's `updated_at`) after an UPDATE. Code that returns a
just-saved object and then reads one of those columns raises `MissingGreenlet`, which surfaces as
an HTTP 500. Mocked tests can never see this (a fake repository has no database), so the only
check is to run the real endpoints against a real PostgreSQL. Three such bugs were found and
fixed earlier; this script is the repeatable proof that none remain on the API's update paths.

It also catches any other unexpected server error on those paths.

Usage (backend running against a SEEDED database, see tools/sandbox_e2e/README.md):
    python tools/sandbox_e2e/audit_update_paths.py [--api http://localhost:8000/api/v1]

Needs: httpx. Creates new records (a job, a candidate, an application, leave requests, a document)
on every run, so run it against a development or sandbox database, never a real one.
Exit code 0 = no 5xx; 1 = at least one endpoint answered 5xx.
"""

import argparse
import datetime
import pathlib
import sys
import time

import httpx

ap = argparse.ArgumentParser()
ap.add_argument("--api", default="http://localhost:8000/api/v1")
args = ap.parse_args()
B = args.api
RESUMES = pathlib.Path(__file__).resolve().parents[2] / "backend" / "seed_data" / "resumes"
PASSWORD = "Demo!Pass123"
STAMP = int(time.time())
# fresh, non-overlapping leave dates on every run
BASE = datetime.date(2028, 1, 1) + datetime.timedelta(days=(STAMP // 10) % 1500)
d = lambda n: (BASE + datetime.timedelta(days=n)).isoformat()  # noqa: E731

c=httpx.Client(base_url=B,timeout=120)
res=[]
def call(label,m,p,tok=None,**kw):
    h={"Authorization":"Bearer "+tok} if tok else {}
    r=c.request(m,p,headers=h,**kw)
    body=None
    try: body=r.json()
    except Exception: body=r.text[:120]
    flag="" if r.status_code<500 else "   <<<<<< 500"
    print(f"{r.status_code}  {label}{flag}")
    res.append((label,r.status_code))
    return r.status_code,body
def login(e): return c.post("/auth/login",json={"email":e,"password":PASSWORD}).json()["access_token"]
emma=login("emma.martin@northwind-robotics.com"); olivia=login("olivia.brown@northwind-robotics.com"); sarah=login("sarah.lopez@candidates-demo.com"); david=login("david.chen@northwind-robotics.com")

print("== jobs")
s,j=call("POST /jobs (create)","POST","/jobs",emma,json={"title":"Audit Engineer","description":"Audit job","employment_type":"full_time","required_skills":["Python"],"preferred_skills":["AWS"],"min_years_experience":2})
jid=j["id"]
s,u=call("PATCH /jobs/{id} (edit)","PATCH",f"/jobs/{jid}",emma,json={"title":"Audit Engineer II","location":"Remote","salary_min":50000,"salary_max":70000,"salary_currency":"EUR"})
print("     edited title ->",u.get("title") if isinstance(u,dict) else u, "| updated_at present:", isinstance(u,dict) and "updated_at" in u)
call("POST /jobs/{id}/transition -> open","POST",f"/jobs/{jid}/transition",emma,json={"target_status":"open"})
s,j2=call("POST /jobs (create 2nd draft)","POST","/jobs",emma,json={"title":"To Delete","description":"x","employment_type":"full_time"})
call("DELETE /jobs/{id} (draft)","DELETE",f"/jobs/{j2['id']}",emma)

print("== candidate + application + resume")
email=f"audit{STAMP}@candidates-demo.com"
s,reg=call("POST /auth/register/candidate","POST","/auth/register/candidate",json={"first_name":"Audit","last_name":"Candidate","email":email,"password":PASSWORD})
ct=reg["access_token"]
pdf=sorted(RESUMES.glob("alex*.pdf"))[0]
s,r=call("POST /resumes (upload)","POST","/resumes",ct,files={"file":(pdf.name,pdf.read_bytes(),"application/pdf")})
rid=r["id"]
s,a=call("POST /applications (apply)","POST","/applications",ct,json={"job_id":jid})
aid=a["id"]
call("PUT /applications/mine/{id}/resume (attach)","PUT",f"/applications/mine/{aid}/resume",ct,json={"resume_id":rid})
time.sleep(6)
call("GET analysis-status (candidate)","GET",f"/applications/mine/{aid}/analysis-status",ct)
call("GET analysis (staff)","GET",f"/applications/{aid}/analysis",emma)
call("POST reanalyze","POST",f"/applications/{aid}/reanalyze",emma)
time.sleep(5)

print("== emails")
s,e=call("POST emails/draft interview_invitation","POST",f"/applications/{aid}/emails/draft",emma,json={"email_type":"interview_invitation"})
eid=e["id"]
s,e2=call("PATCH email (edit draft)","PATCH",f"/applications/{aid}/emails/{eid}",emma,json={"subject":"Edited subject","body":"Edited body text."})
print("     edited subject ->",e2.get("subject") if isinstance(e2,dict) else e2)
call("POST email regenerate","POST",f"/applications/{aid}/emails/{eid}/regenerate",emma)
call("POST email send","POST",f"/applications/{aid}/emails/{eid}/send",emma)
call("PATCH sent email (must refuse)","PATCH",f"/applications/{aid}/emails/{eid}",emma,json={"subject":"x","body":"y"})

print("== stages")
for st in ["screening","interview"]:
    call(f"POST application transition -> {st}","POST",f"/applications/{aid}/transition",emma,json={"target_status":st})
call("POST application transition -> rejected","POST",f"/applications/{aid}/transition",emma,json={"target_status":"rejected"})
call("POST job transition -> closed","POST",f"/jobs/{jid}/transition",emma,json={"target_status":"closed"})
call("POST job transition -> archived","POST",f"/jobs/{jid}/transition",emma,json={"target_status":"archived"})

print("== leave")
s,l=call("POST /leave-requests (create)","POST","/leave-requests",sarah,json={"start_date":d(0),"end_date":d(1),"leave_type":"personal","reason":"audit"})
call("POST leave cancel","POST",f"/leave-requests/{l['id']}/cancel",sarah)
s,l2=call("POST /leave-requests (create 2)","POST","/leave-requests",sarah,json={"start_date":d(10),"end_date":d(11),"leave_type":"sick"})
call("POST leave approve","POST",f"/leave-requests/{l2['id']}/approve",david)
s,l3=call("POST /leave-requests (create 3)","POST","/leave-requests",sarah,json={"start_date":d(20),"end_date":d(21),"leave_type":"vacation"})
call("POST leave reject","POST",f"/leave-requests/{l3['id']}/reject",olivia)

print("== knowledge")
s,d=call("POST knowledge upload","POST","/knowledge/documents",olivia,data={"title":"Audit Doc","category":"policy"},files={"file":("audit.txt","Audit policy. Employees receive 3 audit days per year. Audits are performed quarterly.".encode(),"text/plain")})
did=d["id"]; time.sleep(4)
call("POST knowledge reindex","POST",f"/knowledge/documents/{did}/reindex",olivia)
time.sleep(4)
call("DELETE knowledge document","DELETE",f"/knowledge/documents/{did}",olivia)

print("== compass + users")
call("POST compass (policy)","POST","/compass/ask",emma,json={"message":"How many days of annual leave do I get?"})
call("POST internal-users","POST","/auth/internal-users",olivia,json={"email":f"rec{STAMP}@northwind-robotics.com","first_name":"R","last_name":"S","role":"recruiter","password":PASSWORD})
bad=[x for x in res if x[1]>=500]
print("\nTOTAL",len(res),"calls;",len(bad),"returned 5xx:",bad)
sys.exit(1 if bad else 0)
