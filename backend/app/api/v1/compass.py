"""
Compass endpoint.

Single route, any authenticated role — `Depends(get_current_user)`, not
`require_roles(...)`, because per-role capability restriction already
happens INSIDE Compass (via the Capability Registry). This route's only
job is building the WorkspaceContext and handing it to Compass; it
contains no permission logic of its own, mirroring Compass's own "no
business logic" rule one layer up.

`application_id` is optional on the request (see CompassAskRequest) —
a workspace-independent question (Knowledge Agent) legitimately has no
application in view. `workspace_id` is only set on the context when one
was actually provided; Compass's own routing (see
Compass._resolve_capability_for_role) treats its absence as the signal
that this is a general question, not an error condition here.
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
from app.schemas.knowledge import KnowledgeCitationRead

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
        workspace_type="application" if payload.application_id else None,
        workspace_id=str(payload.application_id) if payload.application_id else None,
        data={"current_user": current_user},
    )

    response = await Compass(db).handle_message(payload.message, context)
    return CompassAskResponse(
        message=response.message,
        capability_used=response.capability_used,
        citations=(
            [KnowledgeCitationRead.model_validate(c, from_attributes=True) for c in response.citations]
            if response.citations
            else None
        ),
        confidence=response.confidence.value if response.confidence else None,
    )
