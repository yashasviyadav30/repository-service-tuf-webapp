# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""What the root history screen receives."""

from pydantic import BaseModel, Field

from app.enums import ExpiryBand, KeyChangeAction


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
