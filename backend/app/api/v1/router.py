"""
API v1 router aggregation.

Every feature slice adds its router here (e.g. `auth.router` in Slice 1,
`jobs.router` in Slice 2). Kept as one aggregation point so `main.py`
never needs to know about individual feature routers.
"""

from fastapi import APIRouter

from app.api.v1.applications import router as applications_router
from app.api.v1.auth import router as auth_router
from app.api.v1.compass import router as compass_router
from app.api.v1.health import router as health_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.public_jobs import router as public_jobs_router
from app.api.v1.resumes import router as resumes_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_v1_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api_v1_router.include_router(public_jobs_router, prefix="/public/jobs", tags=["public"])
api_v1_router.include_router(applications_router, prefix="/applications", tags=["applications"])
api_v1_router.include_router(resumes_router, prefix="/resumes", tags=["resumes"])
api_v1_router.include_router(compass_router, prefix="/compass", tags=["compass"])
