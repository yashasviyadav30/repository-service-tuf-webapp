# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""What the status panel receives."""

from pydantic import BaseModel, Field

from app.enums import RepositoryState


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
