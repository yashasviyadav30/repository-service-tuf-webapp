# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Shared fixtures for the test suite."""

from collections.abc import Iterator

import pytest

from app.config import get_settings


@pytest.fixture(autouse=True)
def deployment_settings(monkeypatch) -> Iterator[None]:
    """Give every test the settings a deployment supplies, freshly read.

    ``get_settings`` holds its answer for the life of the process, which is
    what a deployment wants and what a test cannot have. Without the
    variable the suite would be green only because ``TestClient`` skips the
    lifespan; tests about a missing setting remove it themselves.
    """
    monkeypatch.setenv("RSTUF_METADATA_URL", "http://metadata.example/")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
