"""
OnboardingTask model.

A flat, deliberately unconfigurable checklist — no due dates, no
manager assignment, no progress percentage, no templates. The Product
Book's vision for onboarding (progress bars, configurable templates,
manager meetings scheduling) is real but out of scope for this slice;
what's here is just enough for the hire workflow to leave behind
concrete, inspectable evidence that "create onboarding checklist" ran.

The fixed list of task titles created per employee lives in
`EmployeeService`, not here — this model has no opinion about what
tasks exist, only how to store one.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class OnboardingTask(Base):
    __tablename__ = "onboarding_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<OnboardingTask id={self.id} title={self.title!r} completed={self.completed}>"
