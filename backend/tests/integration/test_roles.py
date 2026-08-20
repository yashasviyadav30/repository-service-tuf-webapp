# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Opening one role, and reading the bytes it was verified from.

A top-level role was checked during the refresh. A delegated one is fetched
and checked when somebody asks for it, which is what keeps a repository of
256 bins from costing 256 requests to draw its first screen.
"""

from __future__ import annotations

import base64
import json
import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.metadata_service import (
    MetadataService,
    get_metadata_service,
)
from tests.base import RepositoryTestCase
from tests.conftest import FIXTURE_ROOT, service_settings


class TestATopLevelRole(RepositoryTestCase):
    """Roles the client resolved while verifying the repository."""

    def test_names_the_keys_root_authorises_for_it(self, webapp) -> None:
        body = webapp("good").get("/api/v1/roles/root").json()

        assert body["name"] == "root"
        assert body["signed_by"][0]["name"] == "root_key_1"
        assert body["signed_by"][0]["online"] is False

    def test_counts_the_signatures_rather_than_assuming_them(
        self, webapp
    ) -> None:
        """The client already accepted this role, so the count necessarily
        meets the threshold. An operator reading "2 of 2" is asking about
        evidence, and the honest answer to "how many" is never "enough"."""
        body = webapp("good").get("/api/v1/roles/root").json()

        assert body["signatures_present"] == body["threshold"] == 2

    def test_lists_the_roles_targets_delegates_to(self, webapp) -> None:
        body = webapp("good").get("/api/v1/roles/targets").json()

        assert sorted(body["delegates_to"]) == ["bins-0", "bins-1"]


class TestADelegatedRole(RepositoryTestCase):
    """Roles fetched on request, and checked by the parent that named them."""

    def test_opening_one_fetches_and_checks_it(self, webapp) -> None:
        body = webapp("good").get("/api/v1/roles/bins-0").json()

        assert body["status"] == "valid"
        assert body["signatures_present"] == 1
        assert body["threshold"] == 1
        assert all(
            item["path"].startswith("bins-0/") for item in body["artifacts"]
        )

    def test_reports_the_key_the_parent_declared(self, webapp) -> None:
        """A delegated role is signed by keys named in its parent, not by a
        top-level key, so the parent is where the signer is read from."""
        body = webapp("good").get("/api/v1/roles/bins-0").json()

        assert body["signed_by"][0]["name"] == "online_key"
        assert body["signed_by"][0]["online"] is True

    def test_says_why_one_older_than_snapshot_pins_is_not_valid(
        self, webapp
    ) -> None:
        body = webapp("rolled-back").get("/api/v1/roles/bins-0").json()

        assert body["status"] == "invalid"
        assert "snapshot pins version 2" in body["signature_note"]


class TestARoleThisRepositoryDoesNotHave(RepositoryTestCase):
    """A name that matches nothing is the caller's mistake, not a failure."""

    def test_answers_404(self, webapp) -> None:
        response = webapp("good").get("/api/v1/roles/not-a-role")

        assert response.status_code == 404

    def test_refuses_a_name_that_could_reach_out_of_the_repository(
        self, webapp
    ) -> None:
        """The name arrives in a URL and is used to build a filename, so it
        is constrained before anything reads it."""
        response = webapp("good").get("/api/v1/roles/..%2Froot")

        assert response.status_code in (404, 422)


class TestTheBytesARoleWasVerifiedFrom(RepositoryTestCase):
    """The link on a role's panel points here, never at the storage.

    A reader may not be able to reach that address, and a fresh fetch from it
    would return whatever is there now, unchecked.
    """

    def test_the_panel_says_where_to_read_them(self, webapp) -> None:
        body = webapp("good").get("/api/v1/roles/root").json()

        assert body["raw_url"] == "/api/v1/roles/root/raw"

    def test_serves_a_top_level_role_from_what_was_verified(
        self, webapp
    ) -> None:
        client = webapp("good")
        described = client.get("/api/v1/roles/targets").json()

        response = client.get(described["raw_url"])
        document = json.loads(response.content)

        assert response.status_code == 200
        # The same version the page reported, not a later fetch of the file.
        assert document["signed"]["version"] == described["version"]
        assert document["signed"]["_type"] == "targets"

    def test_serves_the_root_the_client_settled_on(self, webapp) -> None:
        """The anchor handed over is version one and the chain ends at three.
        What is served is what the client accepted, not what it started
        with."""
        document = json.loads(
            webapp("good").get("/api/v1/roles/root/raw").content
        )

        assert document["signed"]["version"] == 3

    def test_serves_a_delegated_role_it_checked_on_request(
        self, webapp
    ) -> None:
        client = webapp("good")
        described = client.get("/api/v1/roles/bins-0").json()

        document = json.loads(client.get(described["raw_url"]).content)

        assert document["signed"]["version"] == described["version"]
        assert set(document) == {"signed", "signatures"}

    def test_answers_with_the_bytes_and_not_a_rewriting_of_them(
        self, webapp
    ) -> None:
        """A signature covers the layout as much as the content. Parsing the
        document and writing it out again would produce the same fields in
        this library's own formatting, and nobody signed that."""
        served = webapp("good").get("/api/v1/roles/timestamp/raw").content
        published = (FIXTURE_ROOT / "good" / "timestamp.json").read_bytes()

        assert served == published

    def test_hands_the_file_over_rather_than_rendering_it(
        self, webapp
    ) -> None:
        """Metadata comes from a repository this service does not control, so
        it is never returned as something a browser will execute."""
        response = webapp("good").get("/api/v1/roles/root/raw")

        assert response.headers["content-type"].startswith("application/json")
        assert "attachment" in response.headers["content-disposition"]
        assert response.headers["x-content-type-options"] == "nosniff"


class TestABinThatWillNotParse(RepositoryTestCase):
    """Bytes that are not metadata at all, asked for by name.

    The artifact list already leaves such a bin out and names it. Asking for
    that one role has to say so too, rather than raising.
    """

    def test_names_the_trouble_rather_than_crashing(
        self, tmp_path: Path, serve_directory
    ) -> None:
        published = tmp_path / "served"
        shutil.copytree(FIXTURE_ROOT / "good", published)
        (published / "1.bins-0.json").write_bytes(b"not json at all")

        service = MetadataService(
            service_settings(
                metadata_url=serve_directory(published),
                trusted_root=base64.b64encode(
                    (published / "root.json").read_bytes()
                ).decode(),
            )
        )
        app = create_app()
        app.dependency_overrides[get_metadata_service] = lambda: service

        try:
            response = TestClient(app).get("/api/v1/roles/bins-0")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 502
        assert "could not be read" in response.json()["detail"]
