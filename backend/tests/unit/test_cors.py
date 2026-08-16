# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Reaching this API from the interface, which runs somewhere else."""

from fastapi.testclient import TestClient

from app.main import create_app
from tests.base import UnitTestCase

DEV_SERVER = "http://localhost:5173"
NAMED = f"{DEV_SERVER}, http://127.0.0.1:3000"
ALLOW_ORIGIN = "access-control-allow-origin"


def _client(monkeypatch, origins: str) -> TestClient:
    monkeypatch.setenv("RSTUF_CORS_ORIGINS", origins)
    return TestClient(create_app())


class TestCrossOriginAccess(UnitTestCase):
    """Which origins may call this API from a browser."""

    def test_allows_an_origin_a_deployment_named(self, monkeypatch) -> None:
        """The second of two, so a list is read as a list."""
        client = _client(monkeypatch, NAMED)
        origin = "http://127.0.0.1:3000"
        response = client.get("/healthz", headers={"Origin": origin})

        assert response.headers[ALLOW_ORIGIN] == origin

    def test_grants_nothing_by_default(self, monkeypatch) -> None:
        """Unset means the middleware is never attached at all."""
        monkeypatch.delenv("RSTUF_CORS_ORIGINS", raising=False)
        application = create_app()

        attached = [m.cls.__name__ for m in application.user_middleware]
        assert "CORSMiddleware" not in attached

    def test_refuses_an_origin_nobody_named(self, monkeypatch) -> None:
        client = _client(monkeypatch, NAMED)
        response = client.get(
            "/healthz", headers={"Origin": "http://elsewhere.example"}
        )

        assert ALLOW_ORIGIN not in response.headers
