"""
Sub-slice 9c sanity test — mirrors test_hire_workflow_api_wiring.py's
minimalism: proves the leave-request endpoints are actually wired into
the app and require authentication, without a real database or auth
flow.
"""

from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_leave_request_routes_are_registered() -> None:
    schema = app.openapi()
    paths = schema["paths"]
    assert "/api/v1/leave-requests" in paths
    assert "post" in paths["/api/v1/leave-requests"]
    assert "get" in paths["/api/v1/leave-requests"]
    assert "/api/v1/leave-requests/mine" in paths
    assert "/api/v1/leave-requests/mine/balance" in paths
    assert "/api/v1/leave-requests/{leave_request_id}/cancel" in paths
    assert "/api/v1/leave-requests/{leave_request_id}/approve" in paths
    assert "/api/v1/leave-requests/{leave_request_id}/reject" in paths


async def test_create_leave_request_requires_authentication() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/leave-requests",
            json={"start_date": "2026-04-01", "end_date": "2026-04-05", "leave_type": "vacation"},
        )
    assert response.status_code in (401, 403)


async def test_list_leave_requests_requires_authentication() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/leave-requests")
    assert response.status_code in (401, 403)


async def test_approve_leave_request_requires_authentication() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/leave-requests/00000000-0000-0000-0000-000000000000/approve"
        )
    assert response.status_code in (401, 403)
