# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Turning the configured trust anchor into root metadata bytes."""

from __future__ import annotations

import base64
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from app.client.error import MetadataUnavailableError
from app.client.tuf_client import resolve_trusted_root
from tests.base import UnitTestCase

ANCHOR = b'{"signed": {"_type": "root"}}'


class _AnchorHandler(BaseHTTPRequestHandler):
    """Answers /root.json with a redirect, and anything else with ANCHOR."""

    def do_GET(self) -> None:  # noqa: N802 - the base class names it
        if self.path == "/root.json":
            self.send_response(302)
            self.send_header("Location", "/moved.json")
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Length", str(len(ANCHOR)))
        self.end_headers()
        self.wfile.write(ANCHOR)

    def log_message(self, *args: object) -> None:
        """Keep the test output quiet."""


@pytest.fixture
def anchor_server() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _AnchorHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


class TestResolveTrustedRoot(UnitTestCase):
    def test_decodes_inline_metadata(self) -> None:
        resolved = resolve_trusted_root(base64.b64encode(ANCHOR).decode())

        assert resolved == ANCHOR

    def test_rejects_input_that_is_not_base64(self) -> None:
        with pytest.raises(ValueError, match="base64"):
            resolve_trusted_root("this is not base64!")

    def test_reports_an_unreachable_url(self) -> None:
        pointer = base64.b64encode(b"http://127.0.0.1:1/root.json").decode()

        with pytest.raises(MetadataUnavailableError):
            resolve_trusted_root(pointer, timeout=0.5)

    def test_fetches_the_anchor_from_a_url(self, anchor_server) -> None:
        pointer = f"{anchor_server}/moved.json".encode()

        resolved = resolve_trusted_root(base64.b64encode(pointer).decode())

        assert resolved == ANCHOR

    def test_follows_a_redirect_to_the_anchor(self, anchor_server) -> None:
        """Storage is commonly served from behind a redirect, and httpx does
        not follow one unless it is told to."""
        pointer = f"{anchor_server}/root.json".encode()

        resolved = resolve_trusted_root(base64.b64encode(pointer).decode())

        assert resolved == ANCHOR
