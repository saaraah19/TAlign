"""
Communication endpoints.

Nested under the same `/applications` prefix as applications.py (a
separate router, same prefix — kept in its own file per CLAUDE.md's
single-responsibility principle rather than growing applications.py
further). Every route here is an explicit recruiter action; nothing is
triggered automatically by a status transition — see
CommunicationService's module docstring.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.roles import Role
from app.database.session import get_db
from app.models.user import User
from app.schemas.email import DraftEmailRequest, EmailListResponse, EmailRead, UpdateEmailRequest
from app.services.communication_service import CommunicationService

router = APIRouter()

_READ_ROLES = (Role.ADMIN, Role.RECRUITER, Role.HIRING_MANAGER)
_WRITE_ROLES = (Role.ADMIN, Role.RECRUITER)


@router.post("/{application_id}/emails/draft", response_model=EmailRead)
async def draft_email(
    application_id: uuid.UUID,
    payload: DraftEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_WRITE_ROLES)),
) -> EmailRead:
    email = await CommunicationService(db).generate_draft(
        application_id=application_id,
        email_type=payload.email_type.value,
        acting_user=current_user,
    )
    return EmailRead.model_validate(email)


@router.post("/{application_id}/emails/{email_id}/regenerate", response_model=EmailRead)
async def regenerate_email(
    application_id: uuid.UUID,
    email_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_WRITE_ROLES)),
) -> EmailRead:
    email = await CommunicationService(db).regenerate_draft(
        email_id=email_id, acting_user=current_user
    )
    return EmailRead.model_validate(email)


@router.patch("/{application_id}/emails/{email_id}", response_model=EmailRead)
async def update_email(
    application_id: uuid.UUID,
    email_id: uuid.UUID,
    payload: UpdateEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_WRITE_ROLES)),
) -> EmailRead:
    email = await CommunicationService(db).update_draft(
        email_id=email_id, subject=payload.subject, body=payload.body, acting_user=current_user
    )
    return EmailRead.model_validate(email)


@router.post("/{application_id}/emails/{email_id}/send", response_model=EmailRead)
async def send_email(
    application_id: uuid.UUID,
    email_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_WRITE_ROLES)),
) -> EmailRead:
    email = await CommunicationService(db).mark_as_sent(
        email_id=email_id, acting_user=current_user
    )
    return EmailRead.model_validate(email)


@router.get("/{application_id}/emails", response_model=EmailListResponse)
async def list_emails(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_READ_ROLES)),
) -> EmailListResponse:
    emails = await CommunicationService(db).list_for_application(
        application_id=application_id, acting_user=current_user
    )
    return EmailListResponse(items=[EmailRead.model_validate(e) for e in emails])
