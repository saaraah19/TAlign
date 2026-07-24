"""
Compass endpoint.

Single route, any authenticated role — `Depends(get_current_user)`, not
`require_roles(...)`, because per-role capability restriction already
happens INSIDE Compass (via the Capability Registry). This route's only
job is building the WorkspaceContext and handing it to Compass; it
contains no permission logic of its own, mirroring Compass's own "no
business logic" rule one layer up.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.compass.compass import Compass
from app.compass.context import WorkspaceContext
from app.core.roles import Role
from app.database.session import get_db
from app.models.user import User
from app.schemas.compass import CompassAskRequest, CompassAskResponse

router = APIRouter()


@router.post("/ask", response_model=CompassAskResponse)
async def ask_compass(
    payload: CompassAskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompassAskResponse:
    context = WorkspaceContext(
        company_id=str(current_user.company_id) if current_user.company_id else None,
        user_id=str(current_user.id),
        role=Role(current_user.roles[0]) if current_user.roles else Role.CANDIDATE,
        workspace_type="application",
        workspace_id=str(payload.application_id),
        data={"current_user": current_user},
    )

    response = await Compass(db).handle_message(payload.message, context)
    return CompassAskResponse(message=response.message, capability_used=response.capability_used)
