# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Reading root's history and checking its rotations.

The generated repository publishes three versions of root. Version two adds a
second offline key and raises the threshold to two; version three replaces the
online key. Every assertion below reads that chain and not a mock, so a change
to how the walk pairs versions shows up here.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.repositories.root_repository import MAX_HISTORY
from app.services.metadata_service import (
    MetadataService,
    get_metadata_service,
)
from tests.base import RepositoryTestCase
from tests.conftest import FIXTURE_ROOT


def versions_in(body: dict) -> dict[int, dict]:
    return {entry["version"]: entry for entry in body["versions"]}


class TestRootHistory(RepositoryTestCase):
    """What the walk reports for a repository whose chain holds up."""

    def test_reads_every_version_newest_first(self, webapp) -> None:
        body = webapp("good").get("/api/v1/roots").json()

        assert body["current"] == 3
        assert body["earliest"] == 1
        assert [entry["version"] for entry in body["versions"]] == [3, 2, 1]
        assert body["message"] is None

    def test_verifies_each_rotation_against_the_version_before_it(
        self, webapp
    ) -> None:
        body = webapp("good").get("/api/v1/roots").json()
        versions = versions_in(body)

        assert all(entry["verified"] for entry in body["versions"])
        # Version three needed both of version two's keys to authorise it.
        assert versions[3]["by_previous_keys"] == {
            "verified": True,
            "present": 2,
            "threshold": 2,
        }
        # Version one has nothing before it, and says so instead of claiming
        # a check it could not run.
        assert versions[1]["by_previous_keys"] is None
        assert versions[1]["by_own_keys"]["threshold"] == 1

    def test_reports_the_key_a_rotation_added(self, webapp) -> None:
        body = webapp("good").get("/api/v1/roots").json()

        changes = versions_in(body)[2]["keys_changed"]
        assert [(c["name"], c["action"]) for c in changes] == [
            ("root_key_2", "added")
        ]

    def test_reports_a_threshold_that_moved(self, webapp) -> None:
        body = webapp("good").get("/api/v1/roots").json()

        change = next(
            c
            for c in versions_in(body)[2]["roles_changed"]
            if c["role"] == "root"
        )
        assert change["threshold_before"] == 1
        assert change["threshold_after"] == 2
        assert change["signers_added"] == ["root_key_2"]

    def test_reports_an_online_key_being_replaced(self, webapp) -> None:
        """The rotation that matters most in RSTUF: the shared online key is
        swapped, and every role it signed moves to the new one."""
        body = webapp("good").get("/api/v1/roots").json()
        third = versions_in(body)[3]

        actions = {c["name"]: c["action"] for c in third["keys_changed"]}
        assert actions == {
            "online_key": "added",
            "online_key_retired": "removed",
        }

        moved = {c["role"] for c in third["roles_changed"]}
        assert moved == {"timestamp", "snapshot", "targets"}
        assert "root" not in moved

    def test_leaves_untouched_roles_out_of_the_diff(self, webapp) -> None:
        body = webapp("good").get("/api/v1/roots").json()

        # Version two touched root alone. Listing the three unchanged roles
        # beside it would bury the one thing that happened.
        assert [c["role"] for c in versions_in(body)[2]["roles_changed"]] == [
            "root"
        ]

    def test_grades_expiry_only_on_the_version_in_force(self, webapp) -> None:
        """A client checks expiry on the final root alone, so reporting a band
        on a superseded version would raise an alarm about a file nothing
        depends on."""
        versions = versions_in(webapp("good").get("/api/v1/roots").json())

        assert versions[3]["superseded"] is False
        assert versions[3]["band"] == "valid"
        assert versions[1]["superseded"] is True
        assert versions[1]["band"] is None
        assert versions[1]["expires_in"] == "superseded by version 3"

    def test_stops_where_asked_and_says_it_stopped(self, webapp) -> None:
        body = webapp("good").get("/api/v1/roots?limit=2").json()

        assert [entry["version"] for entry in body["versions"]] == [3, 2]
        assert body["earliest"] == 2
        assert "not fetched" in body["message"]

    def test_rejects_a_limit_outside_the_allowed_range(self, webapp) -> None:
        client = webapp("good")

        assert client.get("/api/v1/roots?limit=0").status_code == 422
        assert (
            client.get(f"/api/v1/roots?limit={MAX_HISTORY + 1}").status_code
            == 422
        )


class TestAVersionServedUnderAnotherName(RepositoryTestCase):
    """A genuine root file returned for a version nobody asked for.

    Every signature on it checks out, because the document is real. What
    breaks is the pairing: the walk would check version three's rotation
    against keys that never authorised it, and could report a healthy chain
    as broken or a broken one as healthy. The version inside the file has to
    match the version in its name.

    The anchor here is the current root, which is what a deployment given
    today's root.json holds. python-tuf then has nothing to walk forward to,
    so this walk is the only thing reading the archive.
    """

    def test_stops_the_walk_and_names_what_arrived(
        self, tmp_path: Path, serve_directory
    ) -> None:
        served = tmp_path / "renamed"
        served.mkdir()
        for path in (FIXTURE_ROOT / "good").iterdir():
            served.joinpath(path.name).write_bytes(path.read_bytes())

        # Serve version one's document where version two belongs. Nothing is
        # edited, so it carries its own valid signatures.
        served.joinpath("2.root.json").write_bytes(
            served.joinpath("1.root.json").read_bytes()
        )

        anchor = (served / "3.root.json").read_bytes()
        service = MetadataService(
            Settings(
                metadata_url=serve_directory(served),
                trusted_root=base64.b64encode(anchor).decode(),
            )
        )
        app = create_app()
        app.dependency_overrides[get_metadata_service] = lambda: service

        try:
            body = TestClient(app).get("/api/v1/roots").json()
        finally:
            app.dependency_overrides.clear()

        assert [entry["version"] for entry in body["versions"]] == [3]
        assert "answered with version 1" in body["message"]


class TestAnArchivedRootEditedAfterSigning(RepositoryTestCase):
    """The history check looks where an ordinary refresh does not.

    A client walks forward from the root it already holds, so once it has
    settled on version three it never reads version two again. An archived
    root corrupted or swapped after the fact therefore passes unnoticed.
    Reading the history is what catches it.
    """

    def test_marks_the_step_that_fails_and_keeps_the_rest(
        self, tmp_path: Path, serve_directory
    ) -> None:
        served = tmp_path / "archive"
        served.mkdir()
        for path in (FIXTURE_ROOT / "good").iterdir():
            served.joinpath(path.name).write_bytes(path.read_bytes())

        anchor = (served / "root.json").read_bytes()
        service = MetadataService(
            Settings(
                metadata_url=serve_directory(served),
                trusted_root=base64.b64encode(anchor).decode(),
            )
        )
        app = create_app()
        app.dependency_overrides[get_metadata_service] = lambda: service

        try:
            client = TestClient(app)
            # Settle the client on version three, the way a running one has.
            assert client.get("/api/v1/overview").json()["status"] == "valid"

            # Now edit the archived version two, after signing.
            target = served / "2.root.json"
            document = json.loads(target.read_text(encoding="utf-8"))
            document["signed"]["roles"]["root"]["threshold"] = 3
            target.write_text(json.dumps(document, indent=2), encoding="utf-8")

            body = client.get("/api/v1/roots").json()
        finally:
            app.dependency_overrides.clear()

        versions = versions_in(body)
        # Editing a signed payload invalidates every signature over it.
        assert versions[2]["verified"] is False
        assert versions[2]["by_own_keys"] == {
            "verified": False,
            "present": 0,
            "threshold": 3,
        }

        # The step above it fails too, because version two is what authorises
        # version three. The whole history is still shown.
        assert versions[3]["verified"] is False
        assert versions[3]["by_previous_keys"] == {
            "verified": False,
            "present": 2,
            "threshold": 3,
        }
        assert "rotation into version 3" in versions[3]["note"]
        assert [entry["version"] for entry in body["versions"]] == [3, 2, 1]


class TestSomethingOtherThanRootServedAsRoot(RepositoryTestCase):
    """A genuine document of the wrong kind, under an archived root's name.

    Its signatures check out and it can carry the version that was asked
    for. What it has no part of is a role table, so nothing can be checked
    against it, and asking it to check the version above raises rather than
    answering.
    """

    def test_stops_the_walk_and_names_what_arrived(
        self, tmp_path: Path, serve_directory
    ) -> None:
        served = tmp_path / "swapped"
        served.mkdir()
        for path in (FIXTURE_ROOT / "good").iterdir():
            served.joinpath(path.name).write_bytes(path.read_bytes())

        # Targets metadata, renumbered so the version guard lets it through.
        document = json.loads(
            (served / "1.targets.json").read_text(encoding="utf-8")
        )
        document["signed"]["version"] = 2
        (served / "2.root.json").write_text(
            json.dumps(document, indent=2), encoding="utf-8"
        )

        service = MetadataService(
            Settings(
                metadata_url=serve_directory(served),
                trusted_root=base64.b64encode(
                    (served / "3.root.json").read_bytes()
                ).decode(),
            )
        )
        app = create_app()
        app.dependency_overrides[get_metadata_service] = lambda: service

        try:
            response = TestClient(app).get("/api/v1/roots")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        body = response.json()
        assert [entry["version"] for entry in body["versions"]] == [3]
        assert "Targets metadata" in body["message"]
