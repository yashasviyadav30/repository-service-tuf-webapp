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

import logging
from functools import lru_cache

from app.client.rstuf_api_client import RstufApiClient
from app.client.tuf_client import (
    MetadataUnavailableError,
    RepositoryView,
    load_repository,
    resolve_trusted_root,
)
from app.config import Settings, get_settings
from app.dto.schemas import OverviewResponse, RootsResponse, StatusResponse
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
