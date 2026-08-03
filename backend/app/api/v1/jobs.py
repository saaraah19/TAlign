"""
Jobs endpoints.

Read access (list/get): ADMIN, RECRUITER, HIRING_MANAGER — hiring
managers need to see jobs to review candidates against them, per the
Product Book, but don't create or edit them.
Write access (create/update/delete/transition): ADMIN, RECRUITER only.

This RBAC split is a Slice 2 default, not explicitly specified —
flagged in docs/02_slice2_jobs.md for easy revision if it's wrong.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.roles import Role
from app.database.session import get_db
from app.models.job import JobStatus
from app.models.user import User
from app.schemas.job import (
    JobCreateRequest,
    JobListResponse,
    JobRead,
    JobStatusTransitionRequest,
    JobUpdateRequest,
)
from app.services.job_service import JobService

router = APIRouter()

_READ_ROLES = (Role.ADMIN, Role.RECRUITER, Role.HIRING_MANAGER)
_WRITE_ROLES = (Role.ADMIN, Role.RECRUITER)


@router.post("", response_model=JobRead, status_code=201)
async def create_job(
    payload: JobCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_WRITE_ROLES)),
) -> JobRead:
    job = await JobService(db).create_job(
        acting_user=current_user,
        title=payload.title,
        description=payload.description,
        employment_type=payload.employment_type.value,
        location=payload.location,
        salary_min=payload.salary_min,
        salary_max=payload.salary_max,
        salary_currency=payload.salary_currency.value,
        required_skills=payload.required_skills,
        preferred_skills=payload.preferred_skills,
        min_years_experience=payload.min_years_experience,
    )
    return JobRead.model_validate(job)


@router.get("", response_model=JobListResponse)
async def list_jobs(
    status: JobStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_READ_ROLES)),
) -> JobListResponse:
    jobs, total = await JobService(db).list_jobs(
        acting_user=current_user,
        status=status.value if status else None,
        page=page,
        page_size=page_size,
    )
    return JobListResponse(
        items=[JobRead.model_validate(job) for job in jobs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_READ_ROLES)),
) -> JobRead:
    job = await JobService(db).get_job(job_id=job_id, acting_user=current_user)
    return JobRead.model_validate(job)


@router.patch("/{job_id}", response_model=JobRead)
async def update_job(
    job_id: uuid.UUID,
    payload: JobUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_WRITE_ROLES)),
) -> JobRead:
    update_fields = payload.model_dump(exclude_unset=True)
    if update_fields.get("employment_type") is not None:
        update_fields["employment_type"] = payload.employment_type.value  # type: ignore[union-attr]
    if update_fields.get("salary_currency") is not None:
        update_fields["salary_currency"] = payload.salary_currency.value  # type: ignore[union-attr]

    job = await JobService(db).update_job(job_id=job_id, acting_user=current_user, **update_fields)
    # Same expired-attribute issue as transition_job_status below — see
    # that route's comment for the full explanation.
    full = await JobService(db).get_job(job_id=job.id, acting_user=current_user)
    return JobRead.model_validate(full)


@router.post("/{job_id}/transition", response_model=JobRead)
async def transition_job_status(
    job_id: uuid.UUID,
    payload: JobStatusTransitionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_WRITE_ROLES)),
) -> JobRead:
    job, _event = await JobService(db).transition_status(
        job_id=job_id, target_status=payload.target_status, acting_user=current_user
    )
    # Re-fetch rather than serializing `job` directly: after commit(),
    # `updated_at` (a server-side onupdate=func.now() column) is left
    # expired on the in-memory instance. Reading it synchronously inside
    # Pydantic's model_validate (as opposed to under an explicit await)
    # raised MissingGreenlet here — same reasoning as apply_to_job's and
    # transition_application_status's re-fetch in applications.py.
    full = await JobService(db).get_job(job_id=job.id, acting_user=current_user)
    return JobRead.model_validate(full)


@router.delete("/{job_id}", status_code=204)
async def delete_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_WRITE_ROLES)),
) -> None:
    await JobService(db).delete_job(job_id=job_id, acting_user=current_user)
