# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Read-only calls to the RSTUF API.

The API answers questions the signed metadata cannot: whether the repository
has been set up, and what is waiting to be signed. None of it is a security
claim, so none of it is verified, and a failure here hides one panel and
leaves the service running.

Nothing in this module writes. Changing a repository is the RSTUF API's
own job, reached with the operator's credentials rather than this
service's.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.dto.schemas import RepositoryState

logger = logging.getLogger(__name__)

# RSTUF reports how far a ceremony has progressed. Anything else, including
# no answer at all, means the repository is not ready to be drawn.
_STATE_BY_BOOTSTRAP = {
    "pre": RepositoryState.INITIALISING,
    "signing": RepositoryState.AWAITING_SIGNATURES,
    "finished": RepositoryState.READY,
}


@dataclass
class RepositoryStatus:
    """What the RSTUF API says about the repository right now."""

    available: bool = False
    state: RepositoryState = RepositoryState.NOT_INITIALISED
    bootstrap: str | None = None
    awaiting_signatures: list[str] = field(default_factory=list)
    message: str | None = None


class RstufApiClient:
    """A small client for the handful of endpoints this service reads."""

    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout

    async def _get(self, path: str) -> dict[str, Any] | None:
        """Return a decoded response, or None when the API cannot answer."""
        url = f"{self._base}{path}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.info("RSTUF API did not answer %s: %s", url, exc)
            return None

    async def awaiting_signatures(self) -> list[str]:
        """Name the roles that still need signatures.

        When nothing is pending the API omits the ``data`` field entirely
        instead of sending an empty one. Reading that absence as a list would
        invent a signature request nobody made.
        """
        payload = await self._get("/api/v1/metadata/sign")
        if payload is None:
            return []
        data = payload.get("data") or {}
        metadata = data.get("metadata") or {}
        return sorted(metadata)

    async def status(self) -> RepositoryStatus:
        """Gather everything the status panel shows, in one pass."""
        payload = await self._get("/api/v1/bootstrap/")
        if payload is None:
            return RepositoryStatus(
                available=False,
                message="The RSTUF API could not be reached.",
            )

        data = payload.get("data") or {}
        bootstrap = data.get("state")
        state = _STATE_BY_BOOTSTRAP.get(
            bootstrap or "", RepositoryState.NOT_INITIALISED
        )
        if state is RepositoryState.NOT_INITIALISED and data.get("bootstrap"):
            # Older deployments report the flag without naming a state.
            state = RepositoryState.READY

        pending: list[str] = []
        if state is not RepositoryState.NOT_INITIALISED:
            pending = await self.awaiting_signatures()

        return RepositoryStatus(
            available=True,
            state=state,
            bootstrap=bootstrap,
            awaiting_signatures=pending,
            message=payload.get("message"),
        )
