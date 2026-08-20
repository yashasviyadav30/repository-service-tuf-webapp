# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Walk the history of root, checking every rotation along the way.

Root is the anchor, so rotating a key means publishing a new version of it.
The specification's rotation rule is that version N must be signed to
threshold by the keys of version N-1 *and* by its own keys, which is what
makes a series of root files a chain instead of a pile.

The walk starts at the root the client already verified and moves backwards.
That direction is deliberate. Confirming that version N-1's keys signed
version N proves those keys are the genuine ones, and since N-1 is signed by
those same keys, the whole of N-1 is anchored to something already trusted.
Walking forwards from version 1 would prove nothing, because nothing vouches
for version 1 except itself.
"""

from __future__ import annotations

import asyncio
import logging

from tuf.api.exceptions import RepositoryError
from tuf.api.metadata import Metadata, Root

from app.client.error import MetadataUnavailableError
from app.client.tuf_client import fetch_within
from app.core.constants import DEFAULT_HISTORY, MAX_HISTORY, ROOT_MAX_BYTES
from app.models.roots import RootHistory, RootRevision, SignatureCheck

logger = logging.getLogger(__name__)


def _root_url(metadata_url: str, version: int) -> str:
    """Build the address of one version of root.

    Root files carry their version in the filename whatever the repository's
    consistent-snapshot setting is, so there is no second form to handle.
    """
    base = metadata_url if metadata_url.endswith("/") else metadata_url + "/"
    return f"{base}{version}.root.json"


def _fetch_root_version(
    metadata_url: str, version: int, timeout: float
) -> Metadata:
    """Retrieve one version of root, unverified."""
    url = _root_url(metadata_url, version)
    return Metadata.from_bytes(
        fetch_within(
            url,
            limit=ROOT_MAX_BYTES,
            timeout=timeout,
            what=f"version {version} of root",
        )
    )


def _check_signatures(delegator: Root, child: Metadata) -> SignatureCheck:
    """Ask one version of root whether it authorised the signatures on another.

    ``get_verification_result`` reports the outcome instead of raising it,
    which matters here: a rotation that does not verify is the finding, not an
    error to hide.
    """
    result = delegator.get_verification_result(
        Root.type, child.signed_bytes, child.signatures
    )
    return SignatureCheck(
        verified=result.verified,
        present=len(result.signed),
        threshold=result.threshold,
    )


def _rotation_note(newer: RootRevision, older: RootRevision) -> str | None:
    """Say what went wrong with one step of the chain, when something did."""
    check = newer.by_previous_keys
    if check is None or check.verified:
        return None
    return (
        f"the rotation into version {newer.version} carries {check.present} "
        f"of the {check.threshold} signatures version {older.version} "
        f"requires for it"
    )


def _walk_root_history(
    metadata_url: str,
    trusted: Metadata,
    depth: int,
    timeout: float,
) -> RootHistory:
    """Read backwards from the trusted root, checking each rotation.

    ``depth`` counts versions back from the current one, not an offset: the
    walk always starts at the root the client verified.

    Blocking, so keep it off the event loop.
    """
    current = trusted.signed.version
    newest = RootRevision(
        version=current,
        expires=trusted.signed.expires,
        document=trusted,
        by_own_keys=_check_signatures(trusted.signed, trusted),
    )
    history = RootHistory(current=current, revisions=[newest])

    newer = newest
    for version in range(current - 1, max(0, current - depth), -1):
        try:
            document = _fetch_root_version(metadata_url, version, timeout)
        except MetadataUnavailableError as exc:
            history.message = f"History stops here: {exc}"
            break
        except RepositoryError as exc:
            history.message = (
                f"Version {version} of root could not be read: {exc}"
            )
            break

        # The file has to be the version that was asked for. A server that
        # answers 3.root.json with version 7 would pass every signature
        # check, since the document is genuine, while the rotations were
        # then checked against the wrong pairs.
        # The file has to be root. A repository serving timestamp or targets
        # under this name hands back a genuine, correctly signed document
        # that has no role table to check the next version against, and
        # asking it for one raises rather than answering.
        if not isinstance(document.signed, Root):
            history.message = (
                f"Version {version} of root answered with "
                f"{type(document.signed).__name__} metadata, so the history "
                "stops here"
            )
            break

        if document.signed.version != version:
            history.message = (
                f"Version {version} of root answered with version "
                f"{document.signed.version}, so the history stops here"
            )
            break

        older = RootRevision(
            version=document.signed.version,
            expires=document.signed.expires,
            document=document,
            by_own_keys=_check_signatures(document.signed, document),
        )

        # The older version is what authorises the rotation into the newer
        # one, so the older version is what performs that check.
        newer.by_previous_keys = _check_signatures(
            document.signed, newer.document
        )
        newer.note = newer.note or _rotation_note(newer, older)

        if not older.by_own_keys.verified:
            older.note = (
                f"version {older.version} carries "
                f"{older.by_own_keys.present} of the "
                f"{older.by_own_keys.threshold} signatures it requires"
            )

        history.revisions.append(older)
        newer = older

    if history.message is None and history.earliest > 1:
        history.message = (
            f"Showing versions {history.earliest} to {current}. "
            "Earlier versions exist and were not fetched."
        )

    return history


async def load_root_history(
    metadata_url: str,
    trusted: Metadata,
    depth: int = DEFAULT_HISTORY,
    timeout: float = 10.0,
) -> RootHistory:
    """Read root's history, off the event loop."""
    depth = max(1, min(depth, MAX_HISTORY))
    return await asyncio.to_thread(
        _walk_root_history, metadata_url, trusted, depth, timeout
    )
