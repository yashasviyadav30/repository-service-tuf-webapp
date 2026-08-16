# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""The overview endpoint, against repositories signed with real keys.

Three are generated: one valid, one whose timestamp has lapsed, and one
edited after signing. A signature either checks out or it does not, and this
is the only layer that can tell the difference.
"""

from __future__ import annotations

import base64
import shutil

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services import metadata_service
from app.services.metadata_service import (
    MetadataService,
    get_metadata_service,
)
from tests.base import RepositoryTestCase
from tests.conftest import FIXTURE_ROOT


class TestAHealthyRepository(RepositoryTestCase):
    def test_describes_every_top_level_role(self, webapp) -> None:
        body = webapp("good").get("/api/v1/overview").json()

        assert body["status"] == "valid"
        assert {role["name"] for role in body["roles"]} == {
            "root",
            "timestamp",
            "snapshot",
            "targets",
        }

    def test_orders_roles_the_way_a_client_resolves_them(self, webapp) -> None:
        body = webapp("good").get("/api/v1/overview").json()

        assert [role["name"] for role in body["roles"]][:4] == [
            "root",
            "timestamp",
            "snapshot",
            "targets",
        ]

    def test_reads_thresholds_and_key_names_from_root(self, webapp) -> None:
        """Root asks for two of its two offline keys; the online roles ask
        for one. Reading both proves the threshold comes from root's own
        entry for each role rather than one repository-wide setting."""
        roles = {
            role["name"]: role
            for role in webapp("good").get("/api/v1/overview").json()["roles"]
        }

        assert roles["root"]["threshold"] == 2
        assert roles["root"]["key_count"] == 2
        assert roles["root"]["key_names"] == ["root_key_1", "root_key_2"]
        assert roles["timestamp"]["threshold"] == 1

    def test_names_delegated_roles_without_fetching_them(self, webapp) -> None:
        """Their names come from the rule in targets and their versions from
        snapshot, both already verified. A repository may declare 256."""
        body = webapp("good").get("/api/v1/overview").json()

        delegated = {one["name"] for one in body["delegated"]}
        assert delegated == {"bins-0", "bins-1"}
        assert all(one["version"] is not None for one in body["delegated"])
        # Named, and nothing more: the request that drew this fetched two
        # metadata files, not two hundred and fifty-eight.
        assert "expires" not in body["delegated"][0]

    def test_draws_the_tree_from_the_metadata(self, webapp) -> None:
        body = webapp("good").get("/api/v1/overview").json()
        edges = {(edge["parent"], edge["child"]) for edge in body["edges"]}

        assert ("root", "timestamp") in edges
        assert ("root", "snapshot") in edges
        assert ("root", "targets") in edges
        assert ("targets", "bins-0") in edges

    def test_bands_a_role_by_how_close_it_is_to_expiring(self, webapp) -> None:
        """The generated timestamp carries a one-day life, matching how RSTUF
        renews that role, so it is the band that separates working normally
        from nobody renewing this."""
        roles = {
            role["name"]: role
            for role in webapp("good").get("/api/v1/overview").json()["roles"]
        }

        assert roles["timestamp"]["band"] == "critical"
        assert "expires in" in roles["timestamp"]["expires_in"]

    def test_reports_when_the_repository_was_read(self, webapp) -> None:
        client = webapp("good")
        first = client.get("/api/v1/overview").json()["checked_at"]
        second = client.get("/api/v1/overview").json()["checked_at"]

        # The second answer is the first reading, served again, and must not
        # claim to have been checked at the moment it was served.
        assert first == second


class TestARepositoryInTrouble(RepositoryTestCase):
    """Showing broken trust is the point, so it is a 200 with a status."""

    def test_an_expired_repository_answers_and_says_why(self, webapp) -> None:
        response = webapp("expired").get("/api/v1/overview")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "expired"
        assert "expired" in body["verification_error"].lower()

    def test_a_tampered_repository_names_the_shortfall(self, webapp) -> None:
        response = webapp("tampered").get("/api/v1/overview")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "invalid"
        assert "signed by" in body["verification_error"].lower()

    def test_still_describes_what_it_managed_to_verify(self, webapp) -> None:
        """Verification stops at the first failure, and whatever was checked
        before it is worth showing."""
        body = webapp("expired").get("/api/v1/overview").json()

        assert body["roles"], "nothing was reported at all"


class TestNothingOutlivesItsVerification(RepositoryTestCase):
    """A reading describes the pass that produced it, and nothing else."""

    def test_a_repository_that_stops_verifying_stops_being_described(
        self, tmp_path, serve_directory
    ) -> None:
        """The danger is a screen that looks healthy when it is not.

        Verify a repository, then have the same address serve metadata the
        anchor cannot accept. If the roles, bands and tree from the first
        pass survive into the second answer, stamped with a fresh time,
        nothing on the page says the repository can no longer be verified.
        """
        published = tmp_path / "published"
        shutil.copytree(FIXTURE_ROOT / "good", published)
        anchor = (published / "root.json").read_bytes()

        app = create_app()
        service = MetadataService(
            Settings(
                metadata_url=serve_directory(published),
                trusted_root=base64.b64encode(anchor).decode(),
                # Nothing reused, so this asks about verification rather
                # than about the cache in front of it.
                cache_ttl_seconds=0,
            )
        )
        app.dependency_overrides[get_metadata_service] = lambda: service
        client = TestClient(app)

        healthy = client.get("/api/v1/overview").json()
        assert healthy["status"] == "valid"
        assert len(healthy["roles"]) == 4

        # The same address now serves a repository that fails verification.
        shutil.rmtree(published)
        shutil.copytree(FIXTURE_ROOT / "tampered", published)

        broken = client.get("/api/v1/overview").json()
        app.dependency_overrides.clear()

        assert broken["verification_error"]
        assert "targets" not in {role["name"] for role in broken["roles"]}
        assert broken["delegated"] == []


class TestReadingIsReused(RepositoryTestCase):
    """A visible button is pressed by everyone who arrives, every time."""

    @staticmethod
    def _count_passes(monkeypatch) -> list[int]:
        """Count how many times the repository is actually read."""
        passes: list[int] = []
        original = metadata_service.load_repository

        async def counted(**kwargs):
            passes.append(1)
            return await original(**kwargs)

        monkeypatch.setattr(metadata_service, "load_repository", counted)
        return passes

    def test_a_second_request_does_not_read_the_repository_again(
        self, webapp, monkeypatch
    ) -> None:
        passes = self._count_passes(monkeypatch)

        client = webapp("good")
        client.get("/api/v1/overview")
        client.get("/api/v1/overview")

        assert len(passes) == 1

    def test_a_refresh_within_seconds_is_declined(
        self, webapp, monkeypatch
    ) -> None:
        """Honouring every press would mean a verification pass per visitor
        while the repository has not moved."""
        passes = self._count_passes(monkeypatch)

        client = webapp("good")
        client.get("/api/v1/overview")
        client.get("/api/v1/overview", params={"refresh": "true"})

        assert len(passes) == 1

    def test_a_refresh_is_honoured_once_the_answer_has_aged(
        self, webapp, monkeypatch
    ) -> None:
        """Turning a refresh away is a rate limit, not a refusal."""
        passes = self._count_passes(monkeypatch)
        monkeypatch.setattr(metadata_service, "MIN_REFRESH_SECONDS", 0.0)

        client = webapp("good")
        client.get("/api/v1/overview")
        client.get("/api/v1/overview", params={"refresh": "true"})

        assert len(passes) == 2


class TestNothingToCheckWith(RepositoryTestCase):
    def test_reports_a_missing_trust_anchor_rather_than_guessing(
        self, webapp, serve_fixture
    ) -> None:
        """Showing metadata that was never checked would be worse than
        showing nothing, because it states a falsehood confidently."""
        app = create_app()
        service = MetadataService(
            Settings(metadata_url=serve_fixture("good"), trusted_root=None)
        )
        app.dependency_overrides[get_metadata_service] = lambda: service

        response = TestClient(app).get("/api/v1/overview")
        app.dependency_overrides.clear()

        assert response.status_code == 503
        assert "trust anchor" in response.json()["detail"].lower()
