# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""The operational endpoint, and what happens off the map."""

import importlib
import logging

import pytest
from fastapi.testclient import TestClient

import app.main
from app.main import create_app
from tests.base import UnitTestCase


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


class TestLiveness(UnitTestCase):
    """What the probe answers, and what an unknown path answers."""

    def test_reports_ok(self, client) -> None:
        response = client.get("/healthz")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_an_unknown_path_is_not_found(self, client) -> None:
        response = client.get("/no-such-endpoint")

        assert response.status_code == 404


class TestRequestLogging(UnitTestCase):
    """Every request leaves one line behind, whichever handler answered."""

    def test_records_the_method_path_status_and_duration(
        self, client, caplog
    ) -> None:
        with caplog.at_level(logging.INFO, logger="app.core.logging"):
            client.get("/healthz")

        messages = [record.getMessage() for record in caplog.records]
        assert any("GET /healthz -> 200 in" in line for line in messages)

    def test_records_a_request_whose_handler_raised(self, caplog) -> None:
        app = create_app()

        @app.get("/boom")
        def boom() -> None:
            raise RuntimeError("something went wrong")

        with caplog.at_level(logging.INFO, logger="app.core.logging"):
            TestClient(app, raise_server_exceptions=False).get("/boom")

        messages = [record.getMessage() for record in caplog.records]
        assert any("GET /boom -> 500 in" in line for line in messages)

    def test_the_application_gives_its_records_somewhere_to_go(self) -> None:
        """The tests above pass with or without this, because caplog brings
        a handler of its own. This one does not. Logging is configured when
        the module is imported, so importing it again is the check."""
        saved = logging.root.handlers[:]
        logging.root.handlers.clear()
        try:
            importlib.reload(app.main)
            assert logging.root.handlers
        finally:
            logging.root.handlers[:] = saved
