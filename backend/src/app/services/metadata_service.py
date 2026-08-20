# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""What a request needs, and the order things happen in.

One service holds the settings and the response cache. The per-key lock that
keeps a burst of readers from each starting a verification pass lives on that
cache, so splitting this up would give each part a lock nobody else honours.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from dynaconf import Dynaconf

from app.api.v1.schemas.overview import OverviewResponse
from app.client.error import TrustAnchorMissingError
from app.client.tuf_client import load_repository, resolve_trusted_root
from app.config import get_settings
from app.core.constants import MIN_REFRESH_SECONDS, OVERVIEW_KEY
from app.models.views import RepositoryView
from app.services import presenters
from app.services.cache_service import TTLCache

logger = logging.getLogger(__name__)


class MetadataService:
    """Reads one repository, and reuses the result briefly."""

    def __init__(self, settings: Dynaconf) -> None:
        self._settings = settings
        self._cache = TTLCache(settings.CACHE_TTL_SECONDS)

    def _trust_anchor(self) -> bytes:
        """Establish the one root everything else is checked against.

        Trust-on-first-use is not offered. python-tuf requires an explicit
        bootstrap argument with no default, so the choice cannot be made by
        accident, and taking the anchor from the repository being checked
        would prove nothing anyway.
        """
        if self._settings.TRUSTED_ROOT:
            try:
                return resolve_trusted_root(
                    self._settings.TRUSTED_ROOT,
                    self._settings.REQUEST_TIMEOUT_SECONDS,
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
            metadata_url=self._settings.METADATA_URL,
            bootstrap=self._trust_anchor(),
        )

    async def get_repository_view(
        self, refresh: bool = False
    ) -> RepositoryView:
        """Return a verified view, reusing a recent one unless asked not to.

        A refresh counts only when the answer in hand is old enough that a
        new one could differ. That is a rate limit, not a refusal.
        """
        if refresh:
            age = self._cache.age(OVERVIEW_KEY)
            if age is None or age >= MIN_REFRESH_SECONDS:
                self._cache.clear()
        return await self._cache.get_or_build(OVERVIEW_KEY, self._load)

    async def get_overview(self, refresh: bool = False) -> OverviewResponse:
        """Describe the repository for the first render."""
        return presenters.build_overview(
            await self.get_repository_view(refresh=refresh)
        )


@lru_cache
def get_metadata_service() -> MetadataService:
    """Return the shared service, built once per process."""
    return MetadataService(get_settings())
