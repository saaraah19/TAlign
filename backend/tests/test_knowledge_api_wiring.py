"""
Slice 6 sanity test — mirrors test_health.py's minimalism: proves the
knowledge router is actually wired into the app and its endpoints
require authentication, without spinning up a real database or auth
flow (no other slice's endpoints get full authenticated HTTP-level
tests either — see jobs.py/resumes.py/applications.py, all tested at
the service layer instead; this file stays consistent with that, and
only checks what test_health.py already established a precedent for:
"does the app boot with this router mounted".
"""

from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_knowledge_router_is_registered() -> None:
    schema = app.openapi()
    assert "/api/v1/knowledge/documents" in schema["paths"]
    assert "post" in schema["paths"]["/api/v1/knowledge/documents"]
    assert "get" in schema["paths"]["/api/v1/knowledge/documents"]
    assert "/api/v1/knowledge/documents/{document_id}/reindex" in schema["paths"]


async def test_list_knowledge_documents_requires_authentication() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/knowledge/documents")
    assert response.status_code in (401, 403)


async def test_upload_knowledge_document_requires_authentication() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/knowledge/documents",
            files={"file": ("policy.txt", b"some content", "text/plain")},
            data={"title": "Leave Policy", "category": "policy"},
        )
    assert response.status_code in (401, 403)
