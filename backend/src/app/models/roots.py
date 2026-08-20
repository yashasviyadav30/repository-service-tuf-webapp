# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Root's history, as the walk read it."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from tuf.api.metadata import Metadata


@dataclass
class SignatureCheck:
    """The outcome of one threshold check, with the numbers behind it."""

    verified: bool
    present: int
    threshold: int


@dataclass
class RootRevision:
    """One version of root, and the checks run against it."""

    version: int
    expires: datetime
    document: Metadata
    by_own_keys: SignatureCheck
    by_previous_keys: SignatureCheck | None = None
    note: str | None = None

    @property
    def verified(self) -> bool:
        """True when every check that applies to this version passed.

        Version one has no predecessor it could have rotated from, and nor
        does a version whose predecessor was never fetched. Both are honest
        gaps, recorded as such and never counted as failures.
        """
        if not self.by_own_keys.verified:
            return False
        if self.by_previous_keys is None:
            return True
        return self.by_previous_keys.verified


@dataclass
class RootHistory:
    """Every version of root that was read, newest first."""

    current: int
    revisions: list[RootRevision] = field(default_factory=list)
    message: str | None = None

    @property
    def earliest(self) -> int:
        return self.revisions[-1].version if self.revisions else self.current
