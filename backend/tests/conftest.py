# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Shared fixtures for the test suite."""

import base64
import functools
import http.server
import importlib.util
import json
import os
import socketserver
import tempfile
import threading
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import create_app
from app.services.metadata_service import (
    MetadataService,
    get_metadata_service,
)

BACKEND_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_ROOT = BACKEND_ROOT / "fixtures"
GENERATOR = BACKEND_ROOT / "scripts" / "gen_fixture.py"


def symlinks_permitted() -> bool:
    """Report whether this process may create symbolic links.

    python-tuf caches its trust anchor behind one. Windows refuses that
    without Developer Mode, which makes the client unusable rather than
    merely slower.
    """
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / "target"
        target.write_text("", encoding="utf-8")
        try:
            os.symlink(target, Path(directory) / "link")
        except OSError:
            return False
        return True


def _fixtures_are_usable() -> bool:
    """Report whether the generated repositories are present and in date.

    The valid one carries a short-lived timestamp, matching how RSTUF renews
    that role. Left alone it lapses within a day, which would fail the suite
    for a reason that says nothing about the code.
    """
    timestamp = FIXTURE_ROOT / "good" / "timestamp.json"
    if not timestamp.exists():
        return False

    try:
        document = json.loads(timestamp.read_text(encoding="utf-8"))
        expires = datetime.fromisoformat(document["signed"]["expires"])
    except (OSError, ValueError, KeyError):
        return False

    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return expires > datetime.now(timezone.utc)


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


@pytest.fixture(scope="session", autouse=True)
def generated_repositories() -> None:
    """Rebuild the local repositories when missing or out of date."""
    if _fixtures_are_usable() or not GENERATOR.exists():
        return

    spec = importlib.util.spec_from_file_location("gen_fixture", GENERATOR)
    if spec is None or spec.loader is None:  # pragma: no cover
        return
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()


requires_symlinks = pytest.mark.skipif(
    not symlinks_permitted(),
    reason=(
        "the TUF client requires symbolic links; "
        "enable Developer Mode on Windows"
    ),
)

requires_fixtures = pytest.mark.skipif(
    not GENERATOR.exists(),
    reason="scripts/gen_fixture.py is required to build test repositories",
)


class _ReusableServer(socketserver.TCPServer):
    allow_reuse_address = True


@pytest.fixture
def serve_directory() -> Iterator[object]:
    """Serve a directory of metadata over HTTP and yield its base URL.

    A TUF client is handed a URL, never a directory, so the tests exercise
    the arrangement a deployment uses rather than a shortcut around it.
    """
    servers: list[socketserver.TCPServer] = []

    def _serve(directory: str | Path) -> str:
        handler = functools.partial(
            http.server.SimpleHTTPRequestHandler, directory=str(directory)
        )
        server = _ReusableServer(("127.0.0.1", 0), handler)
        servers.append(server)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return f"http://127.0.0.1:{server.server_address[1]}/"

    yield _serve

    for server in servers:
        server.shutdown()
        server.server_close()


@pytest.fixture
def serve_fixture(serve_directory) -> object:
    """Serve one generated repository and yield its base URL."""

    def _serve(variant: str) -> str:
        return serve_directory(FIXTURE_ROOT / variant)

    return _serve


@pytest.fixture
def bootstrap_root() -> object:
    """Return the trust anchor bytes for a generated repository."""

    def _read(variant: str) -> bytes:
        return (FIXTURE_ROOT / variant / "root.json").read_bytes()

    return _read


@pytest.fixture
def webapp(serve_fixture) -> Iterator[object]:
    """An HTTP client wired to one of the generated repositories."""
    app = create_app()

    def _client(variant: str) -> TestClient:
        anchor = (FIXTURE_ROOT / variant / "root.json").read_bytes()
        service = MetadataService(
            Settings(
                metadata_url=serve_fixture(variant),
                trusted_root=base64.b64encode(anchor).decode(),
            )
        )
        app.dependency_overrides[get_metadata_service] = lambda: service
        return TestClient(app)

    yield _client

    app.dependency_overrides.clear()
