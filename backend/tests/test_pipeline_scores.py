"""Tests for ApplicationService.get_latest_scores — the bulk per-card
score lookup added for the Pipeline Kanban redesign."""

import uuid
from unittest.mock import AsyncMock

from app.services.application_service import ApplicationService


async def test_get_latest_scores_delegates_to_resume_analysis_repository() -> None:
    app_id_1, app_id_2 = uuid.uuid4(), uuid.uuid4()
    resume_analysis_repo = AsyncMock()
    resume_analysis_repo.get_latest_completed_scores.return_value = {app_id_1: 94.0}
    service = ApplicationService(AsyncMock(), resume_analysis_repository=resume_analysis_repo)

    scores = await service.get_latest_scores([app_id_1, app_id_2])

    assert scores == {app_id_1: 94.0}
    resume_analysis_repo.get_latest_completed_scores.assert_awaited_once_with(
        [app_id_1, app_id_2]
    )


async def test_get_latest_scores_with_empty_list_still_delegates() -> None:
    resume_analysis_repo = AsyncMock()
    resume_analysis_repo.get_latest_completed_scores.return_value = {}
    service = ApplicationService(AsyncMock(), resume_analysis_repository=resume_analysis_repo)

    scores = await service.get_latest_scores([])

    assert scores == {}
