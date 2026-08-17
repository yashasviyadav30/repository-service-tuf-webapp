# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Turn verified metadata into the shapes the browser receives.

Nothing here fetches or checks anything. It reads what the client already
verified and presents it: expiry as a band rather than a bare date, keys by
the names RSTUF records for them.
"""

from __future__ import annotations

from datetime import datetime, timezone

from tuf.api.metadata import Metadata

from app.client.tuf_client import RepositoryView
from app.dto.schemas import (
    DelegatedSummary,
    ExpiryBand,
    KeySummary,
    OverviewResponse,
    RoleStatus,
    RoleSummary,
    TreeEdge,
)

# RSTUF records a readable name on each key it publishes, and the address of
# the service holding it where the key is an online one.
RSTUF_KEY_NAME = "x-rstuf-key-name"
RSTUF_ONLINE_KEY_URI = "x-rstuf-online-key-uri"

DAY = 86_400
WEEK = 7 * DAY


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def expiry_band(
    expires: datetime, now: datetime | None = None
) -> tuple[ExpiryBand, str]:
    """Classify how close a role is to expiring, and say it in words."""
    now = now or datetime.now(timezone.utc)
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    seconds = (expires - now).total_seconds()

    if seconds <= 0:
        past = abs(seconds)
        if past < DAY:
            return ExpiryBand.EXPIRED, f"expired {int(past // 3600)}h ago"
        days = int(past // DAY)
        return ExpiryBand.EXPIRED, f"expired {_plural(days, 'day')} ago"

    if seconds < DAY:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return ExpiryBand.CRITICAL, f"expires in {hours}h {minutes}m"

    days = int(seconds // DAY)
    if seconds < WEEK:
        return ExpiryBand.EXPIRING, f"expires in {_plural(days, 'day')}"

    if days > 60:
        return ExpiryBand.VALID, f"expires {expires.date().isoformat()}"
    return ExpiryBand.VALID, f"expires in {_plural(days, 'day')}"


def key_names(root: Metadata | None) -> dict[str, str]:
    """Name every key root declares, falling back to a short identifier.

    A 64-character identifier tells an operator nothing, and RSTUF records a
    readable name on each key it publishes.
    """
    if root is None:
        return {}

    named: dict[str, str] = {}
    for keyid, key in root.signed.keys.items():
        extra = getattr(key, "unrecognized_fields", None) or {}
        named[keyid] = extra.get(RSTUF_KEY_NAME) or keyid[:8]
    return named


def key_summaries(root: Metadata | None) -> dict[str, KeySummary]:
    """Describe every key root declares, by name where RSTUF supplies one.

    Naming is only half of it. RSTUF marks the online keys with the address of
    the service that holds them, which is what makes the offline and online
    split visible to an operator reading the status panel.
    """
    if root is None:
        return {}

    signs: dict[str, list[str]] = {}
    for role_name, role in root.signed.roles.items():
        for keyid in role.keyids:
            signs.setdefault(keyid, []).append(role_name)

    summaries: dict[str, KeySummary] = {}
    for keyid, key in root.signed.keys.items():
        extra = getattr(key, "unrecognized_fields", None) or {}
        summaries[keyid] = KeySummary(
            keyid=keyid,
            keyid_short=keyid[:8],
            name=extra.get(RSTUF_KEY_NAME) or keyid[:8],
            scheme=getattr(key, "scheme", ""),
            online=RSTUF_ONLINE_KEY_URI in extra,
            signs=sorted(signs.get(keyid, [])),
        )
    return summaries


_ROLE_ORDER = {"root": 0, "timestamp": 1, "snapshot": 2, "targets": 3}


def _role_order(name: str) -> tuple[int, str]:
    """Root first, then the order a client resolves them in."""
    return _ROLE_ORDER.get(name, 9), name


def _keyids_for(view: RepositoryView, role_name: str) -> list[str]:
    root = view.documents.get("root")
    if root is None:
        return []
    role = root.signed.roles.get(role_name)
    return list(role.keyids) if role else []


def build_overview(
    view: RepositoryView,
    now: datetime | None = None,
) -> OverviewResponse:
    """Assemble the first render from files the client already verified."""
    now = now or datetime.now(timezone.utc)
    names = key_names(view.documents.get("root"))

    roles: list[RoleSummary] = []
    edges: list[TreeEdge] = []

    for role in view.roles:
        band, phrase = expiry_band(role.expires, now)
        roles.append(
            RoleSummary(
                name=role.name,
                version=role.version,
                expires=role.expires.isoformat(),
                expires_in=phrase,
                band=band,
                threshold=role.threshold,
                key_count=role.key_count,
                key_names=[
                    names[keyid]
                    for keyid in _keyids_for(view, role.name)
                    if keyid in names
                ],
                status=role.status,
            )
        )
        for child in role.delegates_to:
            edges.append(TreeEdge(parent=role.name, child=child))

    # Root authorising the other top-level roles is a delegation too, and the
    # tree is unreadable without it.
    if view.documents.get("root") is not None:
        present = {role.name for role in view.roles}
        edges.extend(
            TreeEdge(parent="root", child=name)
            for name in ("timestamp", "snapshot", "targets")
            if name in present
        )

    status = RoleStatus.VALID
    if view.verification_error:
        status = RoleStatus.EXPIRED if view.expired else RoleStatus.INVALID
    elif any(role.status is RoleStatus.EXPIRED for role in view.roles):
        status = RoleStatus.EXPIRED

    return OverviewResponse(
        status=status,
        checked_at=view.checked_at.isoformat(),
        roles=sorted(roles, key=lambda item: _role_order(item.name)),
        delegated=[
            DelegatedSummary(name=name, version=version)
            for name, version in sorted(view.delegated.items())
        ],
        edges=edges,
        verification_error=view.verification_error,
    )
