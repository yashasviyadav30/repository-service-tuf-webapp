# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""What a request needs, and the order things happen in.

One service holds the settings and the response cache. The lock that keeps a
burst of readers from each starting a verification pass of their own is state
on that cache, so splitting this into several services would give each of
them a lock nobody else honours.
"""

from __future__ import annotations

import asyncio
import logging
from collections import Counter
from functools import lru_cache

from app.client.rstuf_api_client import RstufApiClient
from app.client.tuf_client import (
    DelegatedView,
    MetadataUnavailableError,
    RepositoryView,
    UnknownRoleError,
    load_delegated_role,
    load_repository,
    resolve_trusted_root,
)
from app.config import Settings, get_settings
from app.dto.schemas import (
    ArtifactBinsResponse,
    ArtifactsResponse,
    ArtifactSummary,
    BinSummary,
    OverviewResponse,
    RoleStatus,
    RootsResponse,
    StatusResponse,
)
from app.repositories.root_repository import (
    DEFAULT_HISTORY,
    RootHistory,
    load_root_history,
)
from app.services import presenters
from app.services.cache_service import TTLCache

logger = logging.getLogger(__name__)

OVERVIEW_KEY = "overview"

# How recently the repository must have been read for a refresh to be turned
# away. A visible button is pressed by everyone who arrives, so honouring
# every press means one verification pass per visitor while the repository
# has not moved. RSTUF's worker renews metadata every 5 minutes, so declining
# a second look within 5 seconds gives up nothing.
MIN_REFRESH_SECONDS = 5.0

# How many delegated roles are fetched at once while listing artifacts. A
# repository can hold 256 bins, and asking a storage server for all of them
# in one breath is a burst it did not agree to.
DELEGATED_FETCH_LIMIT = 8


class TrustAnchorMissingError(RuntimeError):
    """No trust anchor could be established, so nothing can be checked."""


class MetadataService:
    """Reads one repository, and reuses the result briefly."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cache = TTLCache(settings.cache_ttl_seconds)
        self._rstuf = (
            RstufApiClient(settings.api_url, settings.request_timeout_seconds)
            if settings.api_url
            else None
        )

    def _trust_anchor(self) -> bytes:
        """Establish the one root everything else is checked against.

        Trust-on-first-use is not offered. python-tuf removed it and now
        requires an explicit bootstrap argument with no default, so the
        choice cannot be made by accident. Taking the anchor from the
        repository being checked would prove nothing anyway.
        """
        if self._settings.trusted_root:
            try:
                return resolve_trusted_root(
                    self._settings.trusted_root,
                    self._settings.request_timeout_seconds,
                )
            except ValueError as exc:
                # Pasting root.json in unencoded is the obvious mistake, and
                # it is a configuration problem rather than a crash.
                raise TrustAnchorMissingError(
                    f"RSTUF_TRUSTED_ROOT could not be read: {exc}"
                ) from exc

        raise TrustAnchorMissingError(
            "No trust anchor is available. Set RSTUF_TRUSTED_ROOT to the "
            "root metadata this deployment should trust."
        )

    async def _load(self) -> RepositoryView:
        """Run one verification pass against the repository."""
        return await load_repository(
            metadata_url=self._settings.metadata_url,
            bootstrap=self._trust_anchor(),
        )

    async def view(self, refresh: bool = False) -> RepositoryView:
        """Return a verified view, reusing a recent one unless asked not to.

        A refresh counts only when the answer in hand is old enough that a
        new one could differ. That is a rate limit, not a refusal.
        """
        if refresh:
            age = self._cache.age(OVERVIEW_KEY)
            if age is None or age >= MIN_REFRESH_SECONDS:
                self._cache.clear()
        return await self._cache.get_or_build(OVERVIEW_KEY, self._load)

    async def overview(self, refresh: bool = False) -> OverviewResponse:
        """Describe the repository for the first render."""
        return presenters.build_overview(await self.view(refresh=refresh))

    async def _delegated(
        self, view: RepositoryView, name: str
    ) -> DelegatedView:
        """Fetch and check one delegated role, explaining a broken chain."""
        if name not in view.delegated and view.verification_error:
            # The delegation list lives in targets, which this repository
            # never got as far as verifying. Saying the role does not exist
            # would be a claim this pass cannot support.
            raise UnknownRoleError(
                f"'{name}' could not be resolved: verification stopped at "
                f"{view.verification_error}"
            )

        return await load_delegated_role(
            self._settings.metadata_url,
            view,
            name,
            self._settings.request_timeout_seconds,
        )

    async def _gather_artifacts(
        self, view: RepositoryView
    ) -> tuple[list[ArtifactSummary], list[str]]:
        """Read every artifact the repository vouches for, once.

        Delegated roles are fetched here because listing artifacts is exactly
        the request that needs their contents. Opening the page is the
        consent; loading them at startup would not be.

        Returns what was read and the names of the roles that could not be.
        Delegated roles are siblings, never a chain, so one unreachable bin
        costs its own artifacts and no others. It is named in the answer,
        because a list quietly short of a hundred entries is worse than a
        list that says which hundred are missing.
        """
        collected: list[ArtifactSummary] = []

        for role in view.roles:
            document = view.documents.get(role.name)
            if document is None:
                continue
            for path, target in getattr(
                document.signed, "targets", {}
            ).items():
                collected.append(
                    ArtifactSummary(
                        path=path,
                        length=target.length,
                        hashes=dict(target.hashes),
                        role=role.name,
                    )
                )

        limiter = asyncio.Semaphore(DELEGATED_FETCH_LIMIT)

        async def fetch(name: str) -> tuple[str, DelegatedView | None]:
            async with limiter:
                try:
                    return name, await self._delegated(view, name)
                except MetadataUnavailableError as exc:
                    logger.info(
                        "Skipping %s while listing artifacts: %s", name, exc
                    )
                    return name, None

        results = await asyncio.gather(
            *(fetch(name) for name in sorted(view.delegated))
        )

        unavailable: list[str] = []
        for name, loaded in results:
            # A role that could not be read and one that did not verify are
            # both roles whose contents nobody should be shown. Listing the
            # second would put artifacts on the page under a signature that
            # failed, or from a version the repository has moved past.
            if loaded is None or loaded.status is not RoleStatus.VALID:
                unavailable.append(name)
                continue
            for path, length, hashes in loaded.artifacts:
                collected.append(
                    ArtifactSummary(
                        path=path, length=length, hashes=hashes, role=name
                    )
                )

        collected.sort(key=lambda item: item.path)
        return collected, unavailable

    async def _artifact_index(
        self, view: RepositoryView
    ) -> tuple[list[ArtifactSummary], list[str]]:
        """Every artifact in the repository, read once and kept.

        Held against the version of snapshot it was read from, because
        snapshot pins every delegated role: a change to any bin moves that
        number. Counting bins, opening one, searching and turning pages all
        read this, so only the first of them asks the storage server.
        """
        snapshot = view.documents.get("snapshot")
        version = getattr(snapshot.signed, "version", 0) if snapshot else 0
        return await self._cache.get_or_build(
            f"artifacts:{version}", lambda: self._gather_artifacts(view)
        )

    async def artifact_bins(self) -> ArtifactBinsResponse:
        """Name every role holding artifacts, with how many it holds.

        The browser asks for this before asking for artifacts, so a
        repository of 256 bins costs one screen of counts instead of a table
        nobody can read.
        """
        view = await self.view()
        collected, unavailable = await self._artifact_index(view)

        counts = Counter(item.role for item in collected)
        # Delegated roles that hold nothing still belong on the list. An
        # operator reading "0" learns the bin exists and is empty, which is
        # not what its absence would have told them.
        names = sorted(set(view.delegated) | set(counts) | set(unavailable))

        return ArtifactBinsResponse(
            total=len(collected),
            bins=[
                BinSummary(
                    name=name,
                    count=counts.get(name, 0),
                    available=name not in unavailable,
                )
                for name in names
            ],
        )

    async def artifacts(
        self,
        search: str = "",
        role: str = "",
        page: int = 1,
        page_size: int = 50,
    ) -> ArtifactsResponse:
        """Return one page of artifacts, from one role or from all of them.

        Narrowing to a role serves the bin a reader has just opened; leaving
        it empty serves a search, which has to span every bin because a name
        gives no clue which one holds it.
        """
        view = await self.view()
        collected, unavailable = await self._artifact_index(view)

        if role:
            # A new list each time, so the cached one is never narrowed in
            # place and the next reader still sees everything.
            collected = [a for a in collected if a.role == role]
        if search:
            needle = search.lower()
            collected = [a for a in collected if needle in a.path.lower()]

        start = max(0, (page - 1) * page_size)
        end = start + page_size
        return ArtifactsResponse(
            total=len(collected),
            page=page,
            page_size=page_size,
            artifacts=collected[start:end],
            unavailable=unavailable,
        )

    async def roots(self, limit: int = DEFAULT_HISTORY) -> RootsResponse:
        """Report root's history, and whether each rotation in it holds up.

        The walk starts from the root the client verified, so the history is
        keyed by that version: publishing a new root retires the cached answer
        instead of leaving a stale chain on the page.
        """
        view = await self.view()
        trusted = view.documents.get("root")
        if trusted is None:
            raise MetadataUnavailableError("root metadata is not available")

        async def build() -> RootHistory:
            return await load_root_history(
                self._settings.metadata_url,
                trusted,
                limit,
                self._settings.request_timeout_seconds,
            )

        history = await self._cache.get_or_build(
            f"roots:{trusted.signed.version}:{limit}", build
        )
        return presenters.build_root_history(history)

    async def status(self) -> StatusResponse:
        """Report live repository status, without letting it break the page."""
        if self._rstuf is None:
            return StatusResponse(
                available=False,
                message="No RSTUF API is configured for this deployment.",
            )

        reported = await self._rstuf.status()
        keys: list = []
        if reported.available:
            # The keys come from root, which the panel shows beside what the
            # API reports. A repository nobody can read still has an API
            # worth reporting on, so failing to read it drops the keys and
            # keeps the rest.
            try:
                view = await self.view()
                root = view.documents.get("root")
                keys = list(presenters.key_summaries(root).values())
            except (MetadataUnavailableError, TrustAnchorMissingError):
                keys = []

        return StatusResponse(
            available=reported.available,
            state=reported.state,
            bootstrap=reported.bootstrap,
            awaiting_signatures=reported.awaiting_signatures,
            keys=keys,
            message=reported.message,
        )


@lru_cache
def get_metadata_service() -> MetadataService:
    """Return the shared service, built once per process."""
    return MetadataService(get_settings())
