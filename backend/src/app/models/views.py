# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""What one verification pass read back."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from tuf.api.metadata import Metadata

from app.enums import RoleStatus


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
    """When this reading was taken, so a cached answer reports its real age."""
