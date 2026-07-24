"""
Slice 0 sanity test.

Deliberately minimal: proves the app boots, the router is wired, and the
health endpoint responds. No business logic exists yet to test.
"""

from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_health_endpoint_reachable() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert "status" in response.json()
