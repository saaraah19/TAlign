"""
Leave requests endpoints (Sub-slice 9c).

Two audiences, two sets of routes — same split as applications.py:
  - Employee-facing (portal self-service): POST "" (create), GET
    "/mine", GET "/mine/balance", POST "/{id}/cancel".
  - Admin/hiring-manager-facing (approval queue): GET "" (optional
    ?status= filter), POST "/{id}/approve", POST "/{id}/reject".

Route ORDER matters here, same reasoning as applications.py: "/mine"
and "/mine/balance" are registered before "/{leave_request_id}/..." so
FastAPI/Starlette matches the literal "/mine" segment before it could
be captured by the "/{leave_request_id}" path parameter pattern.

Not wired into the Dashboard's pending-actions section — confirmed out
of scope for this sub-slice (see the locked spec for 9c).
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.roles import Role
from app.database.session import get_db
from app.models.leave_request import LeaveRequestStatus
from app.models.user import User
from app.schemas.leave_request import (
    LeaveBalanceRead,
    LeaveRequestCreateRequest,
    LeaveRequestListResponse,
    LeaveRequestPipelineListResponse,
    LeaveRequestRead,
    LeaveRequestWithEmployee,
)
from app.services.leave_request_service import LeaveRequestService

router = APIRouter()

_APPROVAL_ROLES = (Role.ADMIN, Role.HIRING_MANAGER)


# --- Employee-facing (portal self-service) ---


@router.post("", response_model=LeaveRequestRead, status_code=201)
async def create_leave_request(
    payload: LeaveRequestCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.EMPLOYEE)),
) -> LeaveRequestRead:
    leave_request = await LeaveRequestService(db).create(
        acting_user=current_user,
        start_date=payload.start_date,
        end_date=payload.end_date,
        leave_type=payload.leave_type,
        reason=payload.reason,
    )
    return LeaveRequestRead.model_validate(leave_request)


@router.get("/mine", response_model=LeaveRequestListResponse)
async def list_my_leave_requests(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.EMPLOYEE)),
) -> LeaveRequestListResponse:
    leave_requests, total = await LeaveRequestService(db).list_mine(
        acting_user=current_user, page=page, page_size=page_size
    )
    return LeaveRequestListResponse(
        items=[LeaveRequestRead.model_validate(r) for r in leave_requests],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/mine/balance", response_model=LeaveBalanceRead)
async def get_my_leave_balance(
    year: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.EMPLOYEE)),
) -> LeaveBalanceRead:
    balance = await LeaveRequestService(db).get_balance(acting_user=current_user, year=year)
    return LeaveBalanceRead(
        year=balance.year,
        annual_allotment=balance.annual_allotment,
        days_used=balance.days_used,
        days_remaining=balance.days_remaining,
    )


@router.post("/{leave_request_id}/cancel", response_model=LeaveRequestRead)
async def cancel_my_leave_request(
    leave_request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.EMPLOYEE)),
) -> LeaveRequestRead:
    leave_request = await LeaveRequestService(db).cancel_mine(
        acting_user=current_user, leave_request_id=leave_request_id
    )
    return LeaveRequestRead.model_validate(leave_request)


# --- Admin/hiring-manager-facing (approval queue) ---


@router.get("", response_model=LeaveRequestPipelineListResponse)
async def list_leave_requests(
    status: LeaveRequestStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_APPROVAL_ROLES)),
) -> LeaveRequestPipelineListResponse:
    leave_requests, total = await LeaveRequestService(db).list_for_company(
        acting_user=current_user,
        status=status.value if status else None,
        page=page,
        page_size=page_size,
    )
    return LeaveRequestPipelineListResponse(
        items=[LeaveRequestWithEmployee.model_validate(r) for r in leave_requests],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/{leave_request_id}/approve", response_model=LeaveRequestWithEmployee)
async def approve_leave_request(
    leave_request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_APPROVAL_ROLES)),
) -> LeaveRequestWithEmployee:
    leave_request = await LeaveRequestService(db).approve(
        acting_user=current_user, leave_request_id=leave_request_id
    )
    return LeaveRequestWithEmployee.model_validate(leave_request)


@router.post("/{leave_request_id}/reject", response_model=LeaveRequestWithEmployee)
async def reject_leave_request(
    leave_request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_APPROVAL_ROLES)),
) -> LeaveRequestWithEmployee:
    leave_request = await LeaveRequestService(db).reject(
        acting_user=current_user, leave_request_id=leave_request_id
    )
    return LeaveRequestWithEmployee.model_validate(leave_request)
