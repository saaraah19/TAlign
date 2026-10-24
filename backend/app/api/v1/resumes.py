"""
Resumes endpoints.

Candidate-only. Attaching a resume to a specific Application is a
separate action on the applications router (PUT /applications/{id}/resume)
— a Resume is owned by the candidate independent of any application; see
app/models/resume.py.
"""

import uuid

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.roles import Role
from app.database.session import get_db
from app.models.user import User
from app.schemas.resume import ResumeRead
from app.services.resume_service import ResumeService

router = APIRouter()


@router.post("", response_model=ResumeRead, status_code=201)
async def upload_resume(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.CANDIDATE)),
) -> ResumeRead:
    content = await file.read()
    resume = await ResumeService(db).upload_resume(
        candidate=current_user,
        filename=file.filename or "resume",
        content_type=file.content_type or "application/octet-stream",
        content=content,
    )
    return ResumeRead.model_validate(resume)


@router.get("/mine", response_model=list[ResumeRead])
async def list_my_resumes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.CANDIDATE)),
) -> list[ResumeRead]:
    resumes = await ResumeService(db).list_my_resumes(candidate=current_user)
    return [ResumeRead.model_validate(r) for r in resumes]


@router.get("/mine/{resume_id}", response_model=ResumeRead)
async def get_my_resume(
    resume_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.CANDIDATE)),
) -> ResumeRead:
    resume = await ResumeService(db).get_my_resume(resume_id=resume_id, candidate=current_user)
    return ResumeRead.model_validate(resume)
