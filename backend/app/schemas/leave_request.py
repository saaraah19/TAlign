"""Leave request schemas (Sub-slice 9c)."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.leave_request import LeaveRequestStatus, LeaveType
from app.schemas.employee import EmployeeRead


class LeaveRequestCreateRequest(BaseModel):
    start_date: date
    end_date: date
    leave_type: LeaveType
    reason: str | None = None


class LeaveRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    company_id: uuid.UUID
    start_date: date
    end_date: date
    leave_type: LeaveType
    reason: str | None
    status: LeaveRequestStatus
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class LeaveRequestWithEmployee(LeaveRequestRead):
    """Admin/hiring-manager-facing: includes the requesting employee's basic info."""

    employee: EmployeeRead


class LeaveRequestListResponse(BaseModel):
    items: list[LeaveRequestRead]
    total: int
    page: int
    page_size: int


class LeaveRequestPipelineListResponse(BaseModel):
    items: list[LeaveRequestWithEmployee]
    total: int
    page: int
    page_size: int


class LeaveBalanceRead(BaseModel):
    year: int
    annual_allotment: int
    days_used: int
    days_remaining: int
