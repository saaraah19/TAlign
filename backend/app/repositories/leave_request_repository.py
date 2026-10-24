"""
LeaveRequest repository.

Two families of read methods, mirroring who's asking — same split as
ApplicationRepository:
  - `*_for_employee`: scoped to one employee's own requests (portal
    "My leave" view).
  - `*_for_company`: scoped to one company's requests, across all its
    employees (admin/hiring-manager approval queue).

`has_overlap` backs LeaveRequestService's overlap-prevention rule. It's
a plain date-range-intersection query (two ranges [a,b] and [c,d]
overlap iff a <= d and c <= b) restricted to PENDING/APPROVED requests
for one employee — a CANCELLED or REJECTED request never occupies
calendar time, so it's excluded from the WHERE clause entirely rather
than fetched and filtered in Python.
"""

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.leave_request import LeaveRequest, LeaveRequestStatus

#: Statuses that occupy calendar time and therefore participate in
#: overlap checks and balance calculations. PENDING counts too — an
#: employee shouldn't be able to stack overlapping requests just
#: because none of them have been decided yet.
_ACTIVE_STATUSES = (LeaveRequestStatus.PENDING.value, LeaveRequestStatus.APPROVED.value)


class LeaveRequestRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, leave_request: LeaveRequest) -> LeaveRequest:
        self._db.add(leave_request)
        await self._db.flush()
        return leave_request

    async def get_by_id_for_employee(
        self, leave_request_id: uuid.UUID, employee_id: uuid.UUID
    ) -> LeaveRequest | None:
        result = await self._db.execute(
            select(LeaveRequest).where(
                LeaveRequest.id == leave_request_id,
                LeaveRequest.employee_id == employee_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_company(
        self, leave_request_id: uuid.UUID, company_id: uuid.UUID
    ) -> LeaveRequest | None:
        result = await self._db.execute(
            select(LeaveRequest)
            .options(selectinload(LeaveRequest.employee))
            .where(
                LeaveRequest.id == leave_request_id,
                LeaveRequest.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_employee(
        self, employee_id: uuid.UUID, *, page: int = 1, page_size: int = 20
    ) -> tuple[list[LeaveRequest], int]:
        base_query = select(LeaveRequest).where(LeaveRequest.employee_id == employee_id)
        count_query = (
            select(func.count())
            .select_from(LeaveRequest)
            .where(LeaveRequest.employee_id == employee_id)
        )
        total = (await self._db.execute(count_query)).scalar_one()
        result = await self._db.execute(
            base_query.order_by(LeaveRequest.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def list_for_company(
        self,
        company_id: uuid.UUID,
        *,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[LeaveRequest], int]:
        base_query = (
            select(LeaveRequest)
            .options(selectinload(LeaveRequest.employee))
            .where(LeaveRequest.company_id == company_id)
        )
        count_query = (
            select(func.count())
            .select_from(LeaveRequest)
            .where(LeaveRequest.company_id == company_id)
        )
        if status is not None:
            base_query = base_query.where(LeaveRequest.status == status)
            count_query = count_query.where(LeaveRequest.status == status)

        total = (await self._db.execute(count_query)).scalar_one()
        result = await self._db.execute(
            base_query.order_by(LeaveRequest.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def has_overlap(
        self,
        employee_id: uuid.UUID,
        start_date: date,
        end_date: date,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> bool:
        query = select(LeaveRequest.id).where(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status.in_(_ACTIVE_STATUSES),
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date,
        )
        if exclude_id is not None:
            query = query.where(LeaveRequest.id != exclude_id)
        result = await self._db.execute(query)
        return result.scalar_one_or_none() is not None

    async def list_approved_in_year(
        self, employee_id: uuid.UUID, year: int
    ) -> list[LeaveRequest]:
        """
        Backs the balance calculation — every APPROVED request whose
        start_date falls in the given calendar year. See
        LeaveRequestService.get_balance for why start_date's year is
        the sole boundary (a request is not expected to span two
        calendar years for the MVP's simple fixed-allotment model).
        """
        result = await self._db.execute(
            select(LeaveRequest).where(
                LeaveRequest.employee_id == employee_id,
                LeaveRequest.status == LeaveRequestStatus.APPROVED.value,
                func.extract("year", LeaveRequest.start_date) == year,
            )
        )
        return list(result.scalars().all())
