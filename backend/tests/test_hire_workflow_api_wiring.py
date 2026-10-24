"""
Slice 7 sanity test — mirrors test_knowledge_api_wiring.py's
minimalism: proves the hire-workflow status endpoint is actually wired
into the app and requires authentication, without a real database or
auth flow.
"""

from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_hire_workflow_status_route_is_registered() -> None:
    schema = app.openapi()
    assert "/api/v1/applications/{application_id}/hire-workflow" in schema["paths"]
    assert "get" in schema["paths"]["/api/v1/applications/{application_id}/hire-workflow"]


async def test_hire_workflow_status_requires_authentication() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/applications/00000000-0000-0000-0000-000000000000/hire-workflow"
        )
    assert response.status_code in (401, 403)
