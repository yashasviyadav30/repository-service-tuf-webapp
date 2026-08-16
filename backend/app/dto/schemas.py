# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Response shapes returned to the browser.

Narrower than the TUF metadata behind them. The interface depends on this
contract, not on the library's internals, so the metadata format can move
without breaking a screen.
"""

from enum import Enum

from pydantic import BaseModel, Field


class RoleStatus(str, Enum):
    """Outcome of verifying one role."""

    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"


class ExpiryBand(str, Enum):
    """How close a role is to expiring.

    Four bands, not two. RSTUF renews timestamp roughly daily, so it sits in
    CRITICAL whenever the repository is healthy; calling that plain VALID
    until the moment it lapses throws away the only useful warning.
    """

    EXPIRED = "expired"
    CRITICAL = "critical"
    EXPIRING = "expiring"
    VALID = "valid"


class ErrorResponse(BaseModel):
    """What every failure from this API carries.

    Declared so it reaches the OpenAPI document. A consumer generating types
    from that document otherwise has no shape for the half of the contract
    that reports trouble.
    """

    detail: str = Field(
        description="Why the request could not be answered",
        examples=["No trust anchor is available."],
    )


class RoleSummary(BaseModel):
    """One verified role, as the table and the tree show it."""

    name: str
    version: int
    expires: str = Field(description="ISO-8601 expiry timestamp")
    expires_in: str = Field(description="The same date, as a phrase")
    band: ExpiryBand
    threshold: int | None = Field(
        default=None, description="Signatures required, where root declares it"
    )
    key_count: int | None = None
    key_names: list[str] = Field(default_factory=list)
    status: RoleStatus


class DelegatedSummary(BaseModel):
    """A delegated role that has not been fetched.

    Its name comes from the delegation rule and its version from snapshot, so
    both are known without downloading anything. A repository may declare two
    hundred and fifty-six of these.
    """

    name: str
    version: int | None = None


class TreeEdge(BaseModel):
    """A delegation from one role to another."""

    parent: str
    child: str


class OverviewResponse(BaseModel):
    """Everything the first render needs, in one request."""

    status: RoleStatus
    checked_at: str = Field(description="When the repository was read")
    roles: list[RoleSummary] = Field(default_factory=list)
    delegated: list[DelegatedSummary] = Field(default_factory=list)
    edges: list[TreeEdge] = Field(default_factory=list)
    verification_error: str | None = Field(
        default=None, description="Why verification stopped, where it did"
    )
