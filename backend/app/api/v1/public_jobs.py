"""
Public job browsing.

Deliberately separate from app/api/v1/jobs.py (the recruiter-facing,
RBAC-gated router): these two endpoints have NO auth dependency at all.
They exist because a candidate obviously needs to see a job before
applying to it, and job listing has been internal-only since Slice 2.

Both endpoints go through JobService's public methods
(`list_open_jobs`, `get_open_job`), which are hard-restricted to
status=OPEN — a draft, closed, or archived job is never visible here,
regardless of company.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.job import JobListResponse, JobRead
from app.services.job_service import JobService

router = APIRouter()


@router.get("", response_model=JobListResponse)
async def list_open_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> JobListResponse:
    jobs, total = await JobService(db).list_open_jobs(page=page, page_size=page_size)
    return JobListResponse(
        items=[JobRead.model_validate(job) for job in jobs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{job_id}", response_model=JobRead)
async def get_open_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> JobRead:
    job = await JobService(db).get_open_job(job_id=job_id)
    return JobRead.model_validate(job)
