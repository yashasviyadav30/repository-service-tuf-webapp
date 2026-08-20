# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""What binds a delegated role's bytes to the name that was asked for.

Under succinct_roles every bin shares one key set and one threshold, so a
signature check cannot tell bins-0 from bins-1. Two other things can: the
entry snapshot records for the role, and the type inside the file.
"""

from __future__ import annotations

import base64
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.client.tuf_client import (
    MetadataUnavailableError,
    load_delegated_role,
    load_repository,
)
from app.enums import RoleStatus
from app.main import create_app
from app.services.metadata_service import (
    MetadataService,
    get_metadata_service,
)
from tests.base import RepositoryTestCase
from tests.conftest import FIXTURE_ROOT, service_settings


class TestOneBinServedAsAnother(RepositoryTestCase):
    """A genuine file returned for a role it does not belong to."""

    @pytest.mark.asyncio
    async def test_a_file_that_is_not_targets_is_refused(
        self, tmp_path: Path, serve_directory, bootstrap_root
    ) -> None:
        published = tmp_path / "published"
        shutil.copytree(FIXTURE_ROOT / "good", published)
        # Answer the request for a bin with root metadata instead. It is
        # genuine and correctly signed; it is simply not a bin.
        shutil.copy(published / "1.root.json", published / "1.bins-0.json")

        url = serve_directory(published)
        view = await load_repository(
            metadata_url=url, bootstrap=bootstrap_root("good")
        )

        with pytest.raises(MetadataUnavailableError, match="not targets"):
            await load_delegated_role(url, view, "bins-0")


class TestABinSnapshotDoesNotList(RepositoryTestCase):
    """Snapshot is what says a role belongs to this repository at all.

    Without an entry there is nothing to check the file against, and
    accepting it would mean taking the file's own word for which role it is.
    """

    @pytest.mark.asyncio
    async def test_a_role_missing_from_snapshot_is_not_valid(
        self, serve_fixture, bootstrap_root
    ) -> None:
        url = serve_fixture("good")
        view = await load_repository(
            metadata_url=url, bootstrap=bootstrap_root("good")
        )
        del view.documents["snapshot"].signed.meta["bins-0.json"]

        delegated = await load_delegated_role(url, view, "bins-0")

        assert delegated.status is RoleStatus.INVALID
        assert "snapshot records nothing" in delegated.note


class TestABinThatWillNotParse(RepositoryTestCase):
    """Bytes that are not metadata at all.

    A repository can serve anything under a bin's name. A role nobody can
    read is a role with nothing to show, which is a fact about the
    repository, not a fault in this service.
    """

    @pytest.mark.asyncio
    async def test_is_reported_rather_than_raised(
        self, tmp_path: Path, serve_directory, bootstrap_root
    ) -> None:
        published = tmp_path / "published"
        shutil.copytree(FIXTURE_ROOT / "good", published)
        (published / "1.bins-0.json").write_bytes(b"not json at all")

        url = serve_directory(published)
        view = await load_repository(
            metadata_url=url, bootstrap=bootstrap_root("good")
        )

        with pytest.raises(
            MetadataUnavailableError, match="could not be read"
        ):
            await load_delegated_role(url, view, "bins-0")

    def test_costs_that_bin_and_no_others(
        self, tmp_path: Path, serve_directory
    ) -> None:
        """One unreadable bin must not take the artifact list down with it."""
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
            listed = TestClient(app).get("/api/v1/artifacts")
        finally:
            app.dependency_overrides.clear()

        assert listed.status_code == 200
        body = listed.json()
        assert body["unavailable"] == ["bins-0"]
        assert {a["role"] for a in body["artifacts"]} == {"bins-1"}
