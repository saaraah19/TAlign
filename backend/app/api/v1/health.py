"""
Health check endpoint.

Deliberately checks real dependencies (DB connectivity), not just "the
process is alive" — a health check that only proves FastAPI is running
is close to useless for deployment readiness checks.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — health check reports, doesn't raise
        db_status = f"error: {exc}"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
    }
