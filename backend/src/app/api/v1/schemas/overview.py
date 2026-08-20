# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""What the first render of the repository receives."""

from pydantic import BaseModel, Field

from app.enums import ExpiryBand, RoleStatus


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
    both are known without downloading anything.
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
