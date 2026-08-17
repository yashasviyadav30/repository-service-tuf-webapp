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


class RepositoryState(str, Enum):
    """How far the repository has progressed through initialisation."""

    READY = "ready"
    NOT_INITIALISED = "not_initialised"
    INITIALISING = "initialising"
    AWAITING_SIGNATURES = "awaiting_signatures"


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


class KeySummary(BaseModel):
    """One signing key, named, since a bare identifier tells nobody much."""

    keyid: str = Field(description="Full key identifier")
    keyid_short: str = Field(description="First 8 characters, for display")
    name: str = Field(description="Readable name, or the short identifier")
    scheme: str = ""
    online: bool = Field(
        default=False,
        description="True when RSTUF records an online key URI for it",
    )
    signs: list[str] = Field(
        default_factory=list, description="Roles this key is authorised for"
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


class StatusResponse(BaseModel):
    """Live repository status, taken from the RSTUF API."""

    available: bool = Field(
        default=False, description="False when the RSTUF API cannot be reached"
    )
    state: RepositoryState = RepositoryState.NOT_INITIALISED
    bootstrap: str | None = None
    awaiting_signatures: list[str] = Field(default_factory=list)
    keys: list[KeySummary] = Field(default_factory=list)
    message: str | None = None


class KeyChangeAction(str, Enum):
    """What a rotation did to one key."""

    ADDED = "added"
    REMOVED = "removed"


class SignatureCheckSummary(BaseModel):
    """One threshold check, reported with the numbers behind it."""

    verified: bool
    present: int = Field(description="Valid signatures found")
    threshold: int = Field(description="Valid signatures required")


class RootKeyChange(BaseModel):
    """One key a rotation introduced or withdrew.

    A key identifier is derived from the key itself, so editing a key
    produces a new identifier. Altering a key therefore appears here as one
    removal and one addition, which is also how a verifier sees it.
    """

    keyid: str
    keyid_short: str
    name: str
    action: KeyChangeAction


class RootRoleChange(BaseModel):
    """How a rotation changed who may sign one role, and how many must."""

    role: str
    threshold_before: int | None = None
    threshold_after: int | None = None
    signers_added: list[str] = Field(default_factory=list)
    signers_removed: list[str] = Field(default_factory=list)


class RootVersionSummary(BaseModel):
    """One version of root, with what it changed and whether it checks out."""

    version: int
    expires: str
    expires_in: str = ""
    band: ExpiryBand | None = Field(
        default=None,
        description=(
            "How close this version is to expiring. Absent once a version "
            "has been superseded, because a client checks expiry only on "
            "the final root, so an old version lapsing means nothing"
        ),
    )
    superseded: bool = Field(
        default=False, description="True for every version but the current one"
    )
    verified: bool = Field(
        description="True when every check that applies to it passed"
    )
    by_own_keys: SignatureCheckSummary
    by_previous_keys: SignatureCheckSummary | None = Field(
        default=None,
        description="Absent for version one, and where the chain stops",
    )
    note: str | None = Field(
        default=None, description="Stated when a check did not pass"
    )
    key_count: int = 0
    keys_changed: list[RootKeyChange] = Field(default_factory=list)
    roles_changed: list[RootRoleChange] = Field(default_factory=list)


class RootsResponse(BaseModel):
    """Root's history, newest version first."""

    current: int = Field(description="The version in force now")
    earliest: int = Field(description="The oldest version read")
    versions: list[RootVersionSummary] = Field(default_factory=list)
    message: str | None = Field(
        default=None,
        description="Stated when the history is partial, and why",
    )
