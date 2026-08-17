# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Listing what the repository vouches for, bin by bin.

The artifacts live in delegated roles, which the client does not fetch while
verifying the top level. Reading them is a second round of fetching, and
these tests drive it against roles signed with real keys.
"""

from __future__ import annotations

from collections import Counter

from app.client.tuf_client import MetadataUnavailableError
from app.services import metadata_service as service_module
from tests.base import RepositoryTestCase


class TestListingArtifacts(RepositoryTestCase):
    """What a page of artifacts holds, and where the entries came from."""

    def test_gathers_them_from_the_delegated_roles(self, webapp) -> None:
        body = (
            webapp("good")
            .get("/api/v1/artifacts", params={"page_size": 500})
            .json()
        )

        assert body["total"] > 0
        assert {a["role"] for a in body["artifacts"]} == {"bins-0", "bins-1"}
        assert body["unavailable"] == []

    def test_carries_the_length_and_hashes_each_bin_declares(
        self, webapp
    ) -> None:
        """A name alone identifies nothing. The entry that makes an artifact
        checkable is the length and the hashes signed alongside it."""
        body = webapp("good").get("/api/v1/artifacts").json()

        first = body["artifacts"][0]
        assert first["length"] > 0
        assert "sha256" in first["hashes"]

    def test_narrows_to_one_bin(self, webapp) -> None:
        body = (
            webapp("good")
            .get(
                "/api/v1/artifacts",
                params={"role": "bins-1", "page_size": 500},
            )
            .json()
        )

        assert body["total"] > 0
        assert {a["role"] for a in body["artifacts"]} == {"bins-1"}

    def test_a_role_that_lists_nothing_is_not_an_error(self, webapp) -> None:
        """The caller asked a question about a name. The honest answer is
        that nothing matches it, the same as a search that finds nothing."""
        body = (
            webapp("good")
            .get("/api/v1/artifacts", params={"role": "bins-99"})
            .json()
        )

        assert body["total"] == 0
        assert body["artifacts"] == []

    def test_filters_by_search_term(self, webapp) -> None:
        body = (
            webapp("good")
            .get("/api/v1/artifacts", params={"search": "urllib3-1.4"})
            .json()
        )

        assert body["total"] == 1
        assert body["artifacts"][0]["role"] == "bins-1"

    def test_pages_the_results(self, webapp) -> None:
        client = webapp("good")
        first = client.get(
            "/api/v1/artifacts", params={"page": 1, "page_size": 10}
        ).json()
        second = client.get(
            "/api/v1/artifacts", params={"page": 2, "page_size": 10}
        ).json()

        assert len(first["artifacts"]) == 10
        assert len(second["artifacts"]) == 10
        # Consecutive pages, not the same ten twice.
        assert {a["path"] for a in first["artifacts"]}.isdisjoint(
            a["path"] for a in second["artifacts"]
        )

    def test_a_default_page_holds_less_than_the_total(self, webapp) -> None:
        """The count and the rows describe different things, so a reader
        given 50 rows beside a total of 64 needs a way to the rest. This is
        the case the generated repository exists to reach."""
        body = webapp("good").get("/api/v1/artifacts").json()

        assert body["total"] > body["page_size"]
        assert len(body["artifacts"]) == body["page_size"]

    def test_rejects_a_page_number_below_one(self, webapp) -> None:
        response = webapp("good").get("/api/v1/artifacts", params={"page": 0})

        assert response.status_code == 422

    def test_rejects_a_role_name_that_could_reach_out_of_the_repository(
        self, webapp
    ) -> None:
        """The name arrives in a query string and is matched against role
        names. It is constrained before anything reads it."""
        response = webapp("good").get(
            "/api/v1/artifacts", params={"role": "../../etc/passwd"}
        )

        assert response.status_code == 422


class TestCountingBins(RepositoryTestCase):
    """The counts the browser asks for before it asks for any artifact."""

    def test_counts_what_each_bin_holds(self, webapp) -> None:
        client = webapp("good")
        bins = client.get("/api/v1/artifacts/bins").json()

        counted = {b["name"]: b["count"] for b in bins["bins"]}
        listed = client.get(
            "/api/v1/artifacts", params={"page_size": 500}
        ).json()

        assert counted == dict(Counter(a["role"] for a in listed["artifacts"]))
        assert bins["total"] == listed["total"]
        assert all(b["available"] for b in bins["bins"])

    def test_names_every_delegated_role_the_repository_declares(
        self, webapp
    ) -> None:
        """A bin holding nothing still belongs on the list. Reading a count
        of zero tells an operator the bin exists and is empty, which is not
        what its absence would have told them."""
        client = webapp("good")
        bins = client.get("/api/v1/artifacts/bins").json()
        overview = client.get("/api/v1/overview").json()

        assert {b["name"] for b in bins["bins"]} == {
            d["name"] for d in overview["delegated"]
        }


class TestABinThatCouldNotBeRead(RepositoryTestCase):
    """One unreachable bin costs its own artifacts and no others.

    Delegated roles are siblings, never a chain. A list quietly short of a
    hundred entries is worse than one saying which hundred are missing.
    """

    def test_names_the_role_and_keeps_the_rest(
        self, webapp, monkeypatch
    ) -> None:
        original = service_module.load_delegated_role

        async def one_bin_fails(metadata_url, view, name, timeout=10.0):
            if name == "bins-1":
                raise MetadataUnavailableError(f"could not fetch {name}")
            return await original(metadata_url, view, name, timeout)

        monkeypatch.setattr(
            service_module, "load_delegated_role", one_bin_fails
        )

        body = webapp("good").get("/api/v1/artifacts").json()

        assert body["unavailable"] == ["bins-1"]
        assert {a["role"] for a in body["artifacts"]} == {"bins-0"}
        assert body["total"] > 0

    def test_reports_it_as_unavailable_rather_than_empty(
        self, webapp, monkeypatch
    ) -> None:
        original = service_module.load_delegated_role

        async def one_bin_fails(metadata_url, view, name, timeout=10.0):
            if name == "bins-1":
                raise MetadataUnavailableError(f"could not fetch {name}")
            return await original(metadata_url, view, name, timeout)

        monkeypatch.setattr(
            service_module, "load_delegated_role", one_bin_fails
        )

        bins = webapp("good").get("/api/v1/artifacts/bins").json()["bins"]
        failed = next(b for b in bins if b["name"] == "bins-1")

        assert failed["available"] is False
        assert failed["count"] == 0


class TestABinOlderThanSnapshotPins(RepositoryTestCase):
    """A correct signature says the file is genuine, not that it is current.

    An old bin signed by the same key verifies perfectly while listing
    artifacts the repository has withdrawn. Snapshot names the version each
    bin should be at, and that entry is what makes the rollback visible.
    """

    def test_leaves_its_artifacts_off_the_page(self, webapp) -> None:
        body = webapp("rolled-back").get("/api/v1/artifacts").json()

        assert body["unavailable"] == ["bins-0"]
        assert "bins-0" not in {a["role"] for a in body["artifacts"]}

    def test_counts_nothing_for_it_and_says_why_it_is_zero(
        self, webapp
    ) -> None:
        bins = webapp("rolled-back").get("/api/v1/artifacts/bins").json()
        rolled = next(b for b in bins["bins"] if b["name"] == "bins-0")

        assert rolled["available"] is False
        assert rolled["count"] == 0


class TestReadingEachBinOnce(RepositoryTestCase):
    """Every artifact lives in a delegated role, so listing them means
    fetching each one. A repository can hold 256, and turning a page must
    not ask the storage server for all of them again.
    """

    def test_paging_and_searching_reuse_one_reading(
        self, webapp, monkeypatch
    ) -> None:
        fetched: list[str] = []
        original = service_module.load_delegated_role

        async def counted(metadata_url, view, name, timeout=10.0):
            fetched.append(name)
            return await original(metadata_url, view, name, timeout)

        monkeypatch.setattr(service_module, "load_delegated_role", counted)

        client = webapp("good")
        client.get("/api/v1/artifacts", params={"page": 1})
        after_first = list(fetched)

        client.get("/api/v1/artifacts", params={"page": 2})
        client.get("/api/v1/artifacts", params={"search": "urllib3"})

        assert sorted(after_first) == ["bins-0", "bins-1"]
        assert fetched == after_first

    def test_counting_bins_costs_nothing_once_they_are_read(
        self, webapp, monkeypatch
    ) -> None:
        """The browser asks for the counts and then the list, in that order,
        and the second must not send the storage server after every bin a
        second time."""
        fetched: list[str] = []
        original = service_module.load_delegated_role

        async def counted(metadata_url, view, name, timeout=10.0):
            fetched.append(name)
            return await original(metadata_url, view, name, timeout)

        monkeypatch.setattr(service_module, "load_delegated_role", counted)

        client = webapp("good")
        client.get("/api/v1/artifacts/bins")
        after_bins = list(fetched)

        client.get("/api/v1/artifacts", params={"role": "bins-0"})

        assert sorted(after_bins) == ["bins-0", "bins-1"]
        assert fetched == after_bins
