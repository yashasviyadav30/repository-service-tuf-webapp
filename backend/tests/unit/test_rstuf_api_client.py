# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Reading the RSTUF API, and the shapes it answers with."""

from __future__ import annotations

from typing import Any

import pytest

from app.client.rstuf_api_client import RstufApiClient
from app.enums import RepositoryState
from tests.base import UnitTestCase


def client_answering(replies: dict[str, Any]) -> RstufApiClient:
    """Return a client whose calls are answered from a dictionary.

    The transport is replaced rather than mocked at the socket, because what
    is under test is how an answer is read, not how it arrives.
    """
    client = RstufApiClient("http://rstuf.invalid")

    async def get(path: str) -> Any:
        return replies.get(path)

    client._get = get
    return client


class TestAnUnreachableApi(UnitTestCase):
    """An API that does not answer must not be read as one saying no.

    The panel it feeds is informational. Turning silence into "this
    repository has not been initialised" would report a fact nobody stated.
    """

    @pytest.mark.asyncio
    async def test_reports_itself_unavailable(self) -> None:
        reported = await client_answering({}).status()

        assert reported.available is False
        assert reported.state is RepositoryState.NOT_INITIALISED
        assert reported.message == "The RSTUF API could not be reached."

    @pytest.mark.asyncio
    async def test_names_no_role_as_awaiting_signatures(self) -> None:
        assert await client_answering({}).awaiting_signatures() == []


class TestBootstrapStates(UnitTestCase):
    """Each state RSTUF reports maps to one this service shows."""

    @pytest.mark.parametrize(
        "reported, expected",
        [
            ("pre", RepositoryState.INITIALISING),
            ("signing", RepositoryState.AWAITING_SIGNATURES),
            ("finished", RepositoryState.READY),
        ],
    )
    @pytest.mark.asyncio
    async def test_maps_a_named_state(
        self, reported: str, expected: RepositoryState
    ) -> None:
        client = client_answering(
            {"/api/v1/bootstrap/": {"data": {"state": reported}}}
        )

        assert (await client.status()).state is expected

    @pytest.mark.asyncio
    async def test_reads_the_flag_where_no_state_is_named(self) -> None:
        """Older deployments answer with the flag and nothing else."""
        client = client_answering(
            {"/api/v1/bootstrap/": {"data": {"bootstrap": True}}}
        )

        assert (await client.status()).state is RepositoryState.READY

    @pytest.mark.asyncio
    async def test_treats_a_state_it_does_not_know_as_uninitialised(
        self,
    ) -> None:
        client = client_answering(
            {"/api/v1/bootstrap/": {"data": {"state": "something-new"}}}
        )

        assert (await client.status()).state is RepositoryState.NOT_INITIALISED


class TestRolesAwaitingSignatures(UnitTestCase):
    """What the signing endpoint answers, and what it leaves out."""

    @pytest.mark.asyncio
    async def test_names_the_roles_pending(self) -> None:
        client = client_answering(
            {
                "/api/v1/bootstrap/": {"data": {"state": "finished"}},
                "/api/v1/metadata/sign": {
                    "data": {"metadata": {"timestamp": {}, "root": {}}}
                },
            }
        )

        assert (await client.status()).awaiting_signatures == [
            "root",
            "timestamp",
        ]

    @pytest.mark.asyncio
    async def test_reads_an_absent_field_as_nothing_pending(self) -> None:
        """With nothing to sign the API omits ``data`` rather than sending
        an empty one, and an absence is not a signature request."""
        client = client_answering({"/api/v1/metadata/sign": {}})

        assert await client.awaiting_signatures() == []

    @pytest.mark.asyncio
    async def test_does_not_ask_about_a_repository_not_yet_set_up(
        self,
    ) -> None:
        """Nothing can be pending on a repository that does not exist, so
        the second call is not made."""
        asked: list[str] = []
        client = client_answering({"/api/v1/bootstrap/": {"data": {}}})
        answered = client._get

        async def record(path: str) -> object:
            asked.append(path)
            return await answered(path)

        client._get = record

        await client.status()

        assert asked == ["/api/v1/bootstrap/"]
