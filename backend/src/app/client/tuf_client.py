# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Fetch and verify a repository's TUF metadata.

Verification is `tuf.ngclient.Updater`'s work. This module reads back what
it accepted; it never validates metadata itself.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import logging
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import httpx
from securesystemslib.exceptions import StorageError
from tuf.api.exceptions import (
    DownloadError,
    ExpiredMetadataError,
    RepositoryError,
)
from tuf.api.metadata import Metadata
from tuf.ngclient import Updater

from app.client.error import MetadataUnavailableError
from app.core.constants import ROOT_MAX_BYTES, UPDATER_CONFIG
from app.enums import TOP_LEVEL_ROLES, RoleStatus
from app.models.views import RepositoryView, RoleView

logger = logging.getLogger(__name__)


def resolve_trusted_root(value: str, timeout: float = 10.0) -> bytes:
    """Turn the configured trust anchor into root metadata bytes.

    Base64, following the RSTUF client's convention, holding either the root
    metadata itself or a URL pointing at it.
    """
    try:
        decoded = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("trusted root is not valid base64") from exc

    text = decoded.decode("utf-8", errors="replace").strip()
    if text.startswith(("http://", "https://")):
        if text.startswith("http://"):
            # Everything else is checked against what this returns, and
            # nothing checks this.
            logger.warning("The trust anchor is fetched over plain HTTP")
        logger.info("Fetching the trust anchor from %s", text)
        return fetch_within(
            text,
            limit=ROOT_MAX_BYTES,
            timeout=timeout,
            what="the trust anchor",
        )

    return decoded


def fetch_within(url: str, *, limit: int, timeout: float, what: str) -> bytes:
    """Fetch a file, and stop reading once it passes ``limit``.

    UpdaterConfig bounds every fetch the library makes. The fetches written
    here are bounded here. Reading a whole response and then measuring it is
    not a bound: by the time the length is known the bytes are already held.

    The declared length is checked first, because a server that is honest
    about being too large saves the transfer entirely. It is not trusted: the
    body is counted as it arrives either way.

    Redirects are followed, as python-tuf's own fetcher does, so the cap
    holds whatever the final response turns out to be.
    """
    received = bytearray()
    too_large = MetadataUnavailableError(
        f"{what} is larger than the {limit} bytes this service will read"
    )

    try:
        with httpx.stream(
            "GET", url, timeout=timeout, follow_redirects=True
        ) as response:
            response.raise_for_status()

            declared = response.headers.get("content-length")
            if declared is not None:
                try:
                    if int(declared) > limit:
                        raise too_large
                except ValueError:
                    # A length that is not a number says nothing, and the
                    # count below does not depend on it.
                    pass

            for chunk in response.iter_bytes():
                received += chunk
                if len(received) > limit:
                    raise too_large
    except httpx.HTTPError as exc:
        raise MetadataUnavailableError(
            f"{what} could not be fetched from {url}"
        ) from exc

    return bytes(received)


def _status_for(metadata: Metadata, now: datetime) -> RoleStatus:
    """Classify a role the client already accepted as correctly signed."""
    return (
        RoleStatus.EXPIRED
        if metadata.signed.expires < now
        else RoleStatus.VALID
    )


def _delegated_names(targets: Metadata) -> list[str]:
    """List the roles `targets` delegates to, in whichever form it uses.

    Named roles or a succinct-roles rule (TAP 15, which is what RSTUF
    publishes). The library resolves both, so no bin count is assumed here.
    """
    delegations = getattr(targets.signed, "delegations", None)
    if delegations is None:
        return []

    if delegations.succinct_roles is not None:
        return list(delegations.succinct_roles.get_roles())

    return list(delegations.roles or [])


def _delegated_versions(
    documents: dict[str, Metadata],
) -> dict[str, int | None]:
    """Name every delegated role and pin its version, fetching nothing.

    Names come from the rule in targets, versions from snapshot. Both are
    already verified, so 256 bins cost nothing to describe.
    """
    targets = documents.get("targets")
    if targets is None:
        return {}

    snapshot = documents.get("snapshot")
    meta = getattr(snapshot.signed, "meta", {}) if snapshot else {}

    versions: dict[str, int | None] = {}
    for name in _delegated_names(targets):
        entry = meta.get(f"{name}.json")
        versions[name] = getattr(entry, "version", None)
    return versions


def _read_trust_directory(
    trust_dir: Path,
) -> tuple[list[RoleView], dict[str, Metadata]]:
    """Describe every role this pass verified."""
    now = datetime.now(timezone.utc)
    views: list[RoleView] = []
    documents: dict[str, Metadata] = {}

    root_path = trust_dir / "root.json"
    root = Metadata.from_file(str(root_path)) if root_path.exists() else None

    for path in sorted(trust_dir.glob("*.json")):
        name = path.stem
        try:
            metadata = Metadata.from_file(str(path))
        # A file that will not parse is not metadata. DeserializationError
        # is a RepositoryError; an unreadable one raises StorageError.
        except (RepositoryError, StorageError):
            logger.warning("Skipping unreadable metadata: %s", path.name)
            continue

        documents[name] = metadata
        role = (
            root.signed.roles.get(name)
            if root and name in TOP_LEVEL_ROLES
            else None
        )

        views.append(
            RoleView(
                name=name,
                version=metadata.signed.version,
                expires=metadata.signed.expires,
                status=_status_for(metadata, now),
                threshold=role.threshold if role else None,
                key_count=len(role.keyids) if role else None,
                delegates_to=(
                    _delegated_names(metadata) if name == "targets" else []
                ),
            )
        )

    return views, documents


def _refresh(
    trust_dir: Path, metadata_url: str, bootstrap: bytes | None
) -> None:
    """Run the verification pass. Blocking; keep it off the event loop."""
    updater = Updater(
        metadata_dir=str(trust_dir),
        metadata_base_url=metadata_url,
        bootstrap=bootstrap,
        config=UPDATER_CONFIG,
    )
    updater.refresh()


async def load_repository(
    metadata_url: str,
    bootstrap: bytes | None,
) -> RepositoryView:
    """Verify the repository and describe what was found.

    Metadata that fails verification is reported, not raised: showing a
    repository in trouble is the point. Only an unreachable one raises.

    The trust directory is made for this pass and removed after it, so no
    reading can be answered from files an earlier pass left behind.
    """
    verification_error: str | None = None
    expired = False
    trust_dir = Path(tempfile.mkdtemp(prefix="rstuf-verify-"))

    try:
        try:
            # Updater does synchronous I/O. Awaiting it directly would hold
            # the event loop for the length of a fetch.
            await asyncio.to_thread(
                _refresh, trust_dir, metadata_url, bootstrap
            )
        except DownloadError as exc:
            raise MetadataUnavailableError(str(exc)) from exc
        except RepositoryError as exc:
            # Expired, unsigned, or rolled back. What verified before the
            # failure is on disk, so the screen can show how far it got.
            verification_error = str(exc)
            expired = isinstance(exc, ExpiredMetadataError)
            logger.info("Repository failed verification: %s", exc)

        roles, documents = _read_trust_directory(trust_dir)
    finally:
        shutil.rmtree(trust_dir, ignore_errors=True)

    if not roles and verification_error:
        raise MetadataUnavailableError(verification_error)

    return RepositoryView(
        roles=roles,
        verification_error=verification_error,
        expired=expired,
        documents=documents,
        delegated=_delegated_versions(documents),
    )
