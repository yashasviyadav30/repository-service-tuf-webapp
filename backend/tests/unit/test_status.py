# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""The status endpoint, and the deployments that have no API to ask."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.enums import RepositoryState
from app.main import create_app
from app.models.status import RepositoryStatus
from app.services.metadata_service import (
    MetadataService,
    get_metadata_service,
)
from tests.base import UnitTestCase
from tests.conftest import service_settings


def service_without_an_api() -> MetadataService:
    return MetadataService(
        service_settings(metadata_url="http://metadata.example/")
    )


def client_for(service: MetadataService) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_metadata_service] = lambda: service
    return TestClient(app)


class TestADeploymentWithNoApi(UnitTestCase):
    """RSTUF_API_URL is optional, and leaving it out is a valid deployment.

    The metadata is served as files, so a repository can be read with no API
    in reach at all. The panel disappears; the page does not.
    """

    @pytest.mark.asyncio
    async def test_reports_that_none_is_configured(self) -> None:
        reported = await service_without_an_api().get_status()

        assert reported.available is False
        assert reported.state is RepositoryState.NOT_INITIALISED
        assert reported.message == (
            "No RSTUF API is configured for this deployment."
        )

    def test_answers_200_rather_than_an_error(self) -> None:
        response = client_for(service_without_an_api()).get("/api/v1/status")

        assert response.status_code == 200
        assert response.json()["available"] is False


class TestAnApiThatCannotBeReached(UnitTestCase):
    """An API that is configured but silent behaves the same way.

    Status is informational. A repository whose signatures verify is worth
    showing whether or not the service that manages it answered.
    """

    def test_answers_200_and_names_no_keys(self, monkeypatch) -> None:
        service = MetadataService(
            service_settings(
                metadata_url="http://metadata.example/",
                api_url="http://rstuf.invalid/",
            )
        )

        async def unreachable() -> RepositoryStatus:
            return RepositoryStatus(
                available=False, message="The RSTUF API could not be reached."
            )

        monkeypatch.setattr(service._rstuf, "status", unreachable)

        response = client_for(service).get("/api/v1/status")

        assert response.status_code == 200
        body = response.json()
        assert body["available"] is False
        assert body["keys"] == []

    def test_does_not_read_the_repository_at_all(self, monkeypatch) -> None:
        """Reading it would cost a verification pass to fill a panel that is
        already known to be empty."""
        service = MetadataService(
            service_settings(
                metadata_url="http://metadata.example/",
                api_url="http://rstuf.invalid/",
            )
        )

        async def unreachable() -> RepositoryStatus:
            return RepositoryStatus(available=False)

        async def refuse() -> None:
            raise AssertionError("the repository was read")

        monkeypatch.setattr(service._rstuf, "status", unreachable)
        monkeypatch.setattr(service, "get_repository_view", refuse)

        assert client_for(service).get("/api/v1/status").status_code == 200
