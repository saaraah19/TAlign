"""User-related schemas, reused beyond just the auth flows."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.enums import UserStatus
from app.core.roles import AccountType


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID | None
    account_type: AccountType
    email: str
    first_name: str
    last_name: str
    avatar_url: str | None
    status: UserStatus
    roles: list[str]
    created_at: datetime
