# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Fixed sets of values used across the service."""

from enum import Enum

TOP_LEVEL_ROLES = ("root", "timestamp", "snapshot", "targets")


class RoleStatus(str, Enum):
    """Outcome of verifying one role."""

    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"


class ExpiryBand(str, Enum):
    """How close a role is to expiring.

    Four bands, not two. RSTUF renews timestamp roughly daily, so it sits in
    CRITICAL whenever the repository is healthy.
    """

    EXPIRED = "expired"
    CRITICAL = "critical"
    EXPIRING = "expiring"
    VALID = "valid"


class RepositoryState(str, Enum):
    """How far the repository has progressed through initialisation."""

    READY = "ready"
    NOT_INITIALISED = "not_initialised"
    INITIALISING = "initialising"
    AWAITING_SIGNATURES = "awaiting_signatures"
