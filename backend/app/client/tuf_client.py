# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Fetch and verify a repository's TUF metadata.

Verification is `tuf.ngclient.Updater`'s work, not ours. It resolves the
metadata chain and checks signatures, thresholds, expiry and rollback,
writing what it accepted into a local trust directory. This module reads
those files back; it never validates metadata itself.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import logging
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import httpx
from securesystemslib.exceptions import StorageError
from tuf.api.exceptions import (
    DownloadError,
    ExpiredMetadataError,
    LengthOrHashMismatchError,
    RepositoryError,
)
from tuf.api.metadata import Metadata, Targets
from tuf.ngclient import Updater, UpdaterConfig

from app.dto.schemas import RoleStatus

logger = logging.getLogger(__name__)

TOP_LEVEL_ROLES = ("root", "timestamp", "snapshot", "targets")

# The library's own cap for root metadata, applied to the anchor too.
ROOT_MAX_BYTES = 512_000

# A delegated role holds artifact entries rather than a role table, so it is
# allowed more room than root. Bounded all the same: the file is fetched by
# code written here, and a storage server decides how large it is.
DELEGATED_MAX_BYTES = 5_000_000


class UnknownRoleError(LookupError):
    """The requested role is not delegated by this repository."""


class MetadataUnavailableError(RuntimeError):
    """The metadata could not be retrieved at all.

    Not the same as metadata that arrived and failed verification. Broken
    trust is what this service exists to show; an unreachable repository
    leaves nothing to show.
    """


@dataclass
class RoleView:
    """One verified role, read back from the trust directory."""

    name: str
    version: int
    expires: datetime
    status: RoleStatus
    threshold: int | None = None
    key_count: int | None = None
    delegates_to: list[str] = field(default_factory=list)


@dataclass
class DelegatedView:
    """One delegated role, fetched on request and checked by its parent."""

    name: str
    version: int
    expires: datetime
    status: RoleStatus
    threshold: int
    signed_count: int
    signing_keyids: list[str] = field(default_factory=list)
    delegates_to: list[str] = field(default_factory=list)
    artifacts: list[tuple[str, int, dict[str, str]]] = field(
        default_factory=list
    )
    note: str | None = None
    raw: bytes = b""
    """The bytes that were checked, kept so they can be shown unaltered."""


@dataclass
class RepositoryView:
    """The repository, as far as it could be resolved."""

    roles: list[RoleView] = field(default_factory=list)
    verification_error: str | None = None
    expired: bool = False
    """Whether verification stopped because something had lapsed.

    Taken from the exception type the library raised, not from its message.
    Those messages are not an interface and can be reworded in a release.
    """
    documents: dict[str, Metadata] = field(default_factory=dict)
    delegated: dict[str, int | None] = field(default_factory=dict)
    checked_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    """When this reading was taken.

    Recorded on the reading, because it is served from a cache long after it
    was built and the page reports its age. Deriving that later samples two
    clocks and disagrees with itself.
    """


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
    not a bound: by the time the length is known the bytes are already held,
    and how many there are was decided by a storage server this service does
    not control.

    The declared length is checked first, because a server that is honest
    about being too large saves the transfer entirely. It is not trusted: the
    body is counted as it arrives either way.
    """
    received = bytearray()
    too_large = MetadataUnavailableError(
        f"{what} is larger than the {limit} bytes this service will read"
    )

    try:
        with httpx.stream("GET", url, timeout=timeout) as response:
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

    A delegation is declared either as named roles or as a succinct-roles
    rule that generates them (TAP 15, which is what RSTUF publishes). The
    library resolves both, so no naming scheme or bin count is assumed here.
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

    Names come from the rule in targets, versions from snapshot. Both files
    are already verified, so 256 bins cost nothing to describe.
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


# What the client will accept from a storage server nobody here controls.
# The length caps are generous for real metadata: a 256-bin repository has
# a snapshot listing every bin and is nowhere near 2 MB.
#
# max_root_rotations is what makes pinning a root once and leaving it safe.
# The client walks forward from the version it holds, checking each rotation
# against the one before it, and this is how far it will walk.
UPDATER_CONFIG = UpdaterConfig(
    max_root_rotations=256,
    max_delegations=32,
    root_max_length=512_000,
    timestamp_max_length=16_384,
    snapshot_max_length=2_000_000,
    targets_max_length=5_000_000,
    app_user_agent="rstuf-webapp/0.1.0",
)


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
    repository in trouble is the point. Only an unreachable one raises,
    because then there is nothing to show.

    The client writes what it accepts into a directory made for this pass
    and removed after it. One that outlived the pass would answer with roles
    verified some time ago, stamped with the time of the request that found
    them lying there, and anything else left in it would be read as a role.
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


def _delegated_url(
    metadata_url: str, name: str, version: int | None, consistent: bool
) -> str:
    """Build the address of one delegated role's metadata file."""
    base = metadata_url if metadata_url.endswith("/") else metadata_url + "/"
    filename = quote(f"{name}.json", safe="")
    if consistent and version is not None:
        return f"{base}{version}.{filename}"
    return f"{base}{filename}"


def _pin_mismatch(
    view: RepositoryView,
    name: str,
    child: Metadata,
    raw: bytes,
) -> str | None:
    """Check a delegated role against the entry snapshot pins for it.

    A correct signature says the file is genuine. It does not say the file is
    current, and an old bin signed by the same key verifies perfectly while
    listing artifacts that were withdrawn. Snapshot names the version, and
    where the repository publishes them, the length and hashes. That entry is
    what makes rollback visible, so it is checked and not merely read to
    build a URL.

    Returns the wording for the mismatch, or ``None`` when it agrees.
    """
    snapshot = view.documents.get("snapshot")
    meta = (
        getattr(snapshot.signed, "meta", {}).get(f"{name}.json")
        if snapshot
        else None
    )
    if meta is None:
        # python-tuf refuses a delegated role snapshot does not list, and so
        # does this. Without that entry there is nothing to check the file
        # against, and accepting it would mean trusting the file's own word
        # for which role it is and which version.
        return f"snapshot records nothing for {name}"

    if meta.version is not None and child.signed.version != meta.version:
        return (
            f"{name} is at version {child.signed.version}, and snapshot "
            f"pins version {meta.version}"
        )

    try:
        meta.verify_length_and_hashes(raw)
    except LengthOrHashMismatchError as exc:
        return f"{name} does not match what snapshot records for it: {exc}"

    return None


def _fetch_delegated(
    metadata_url: str,
    view: RepositoryView,
    name: str,
    timeout: float,
) -> DelegatedView:
    """Fetch one delegated role and have its parent check it.

    The parent holds the delegation rule, so the parent does the checking.
    This uses the library's public verification interface, which also reports
    how many of the required signatures were present.
    """
    # Whether the name is a role at all is settled before anything is
    # fetched, so a nonsense name gets a nonsense-name answer. Nothing here
    # reports it as an infrastructure failure.
    if name not in view.delegated:
        raise UnknownRoleError(name)

    targets = view.documents.get("targets")
    if targets is None:
        raise MetadataUnavailableError("targets metadata is not available")

    root = view.documents.get("root")
    consistent = bool(
        getattr(root.signed, "consistent_snapshot", True) if root else True
    )
    url = _delegated_url(
        metadata_url, name, view.delegated.get(name), consistent
    )

    # Kept, because these are the bytes the parent is about to check, and
    # the bytes this service will serve if anyone asks to see the file.
    raw = fetch_within(
        url, limit=DELEGATED_MAX_BYTES, timeout=timeout, what=name
    )
    child: Metadata = Metadata.from_bytes(raw)
    if not isinstance(child.signed, Targets):
        raise MetadataUnavailableError(
            f"{url} is {type(child.signed).__name__} metadata, not targets"
        )

    result = targets.signed.get_verification_result(
        name, child.signed_bytes, child.signatures
    )
    pinned = _pin_mismatch(view, name, child, raw)

    now = datetime.now(timezone.utc)
    if not result.verified:
        status = RoleStatus.INVALID
        note = (
            f"{name} was signed by {len(result.signed)} of "
            f"{result.threshold} required keys"
        )
    elif pinned is not None:
        status = RoleStatus.INVALID
        note = pinned
    elif child.signed.expires < now:
        status = RoleStatus.EXPIRED
        note = None
    else:
        status = RoleStatus.VALID
        note = None

    artifacts = [
        (path, target.length, dict(target.hashes))
        for path, target in getattr(child.signed, "targets", {}).items()
    ]

    return DelegatedView(
        name=name,
        version=child.signed.version,
        expires=child.signed.expires,
        status=status,
        threshold=result.threshold,
        signed_count=len(result.signed),
        signing_keyids=sorted(result.signed) + sorted(result.unsigned),
        delegates_to=_delegated_names(child),
        artifacts=sorted(artifacts),
        note=note,
        raw=raw,
    )


async def load_delegated_role(
    metadata_url: str,
    view: RepositoryView,
    name: str,
    timeout: float = 10.0,
) -> DelegatedView:
    """Load one delegated role, off the event loop."""
    return await asyncio.to_thread(
        _fetch_delegated, metadata_url, view, name, timeout
    )
