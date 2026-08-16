# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Starting a deployment, configured and not."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import create_app
from tests.base import UnitTestCase


class TestStartup(UnitTestCase):
    def test_a_missing_metadata_url_stops_the_server(
        self, monkeypatch
    ) -> None:
        monkeypatch.delenv("RSTUF_METADATA_URL", raising=False)

        with pytest.raises(ValidationError, match="metadata_url"):
            with TestClient(create_app()):
                pass

    def test_a_configured_deployment_starts(self, monkeypatch) -> None:
        monkeypatch.setenv("RSTUF_METADATA_URL", "http://metadata.example/")

        with TestClient(create_app()) as client:
            assert client.get("/healthz").status_code == 200
