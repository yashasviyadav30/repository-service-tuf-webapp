# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""What binds a delegated role's bytes to the name that was asked for.

Under succinct_roles every bin shares one key set and one threshold, so a
signature check cannot tell bins-0 from bins-1. Two other things can: the
entry snapshot records for the role, and the type inside the file.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from app.client.tuf_client import (
    MetadataUnavailableError,
    load_delegated_role,
    load_repository,
)
from app.dto.schemas import RoleStatus
from tests.base import RepositoryTestCase
from tests.conftest import FIXTURE_ROOT


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
