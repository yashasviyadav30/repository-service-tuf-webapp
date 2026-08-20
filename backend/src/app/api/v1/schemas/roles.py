# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""What the role panel receives."""

from pydantic import BaseModel, Field

from app.api.v1.schemas.artifacts import ArtifactSummary
from app.api.v1.schemas.status import KeySummary
from app.enums import ExpiryBand, RoleStatus


class RoleDetailResponse(BaseModel):
    """One role, opened."""

    name: str
    version: int
    expires: str
    expires_in: str = ""
    band: ExpiryBand = ExpiryBand.VALID
    status: RoleStatus
    threshold: int | None = None
    signed_by: list[KeySummary] = Field(default_factory=list)
    signatures_present: int | None = Field(
        default=None, description="Valid signatures found on this role"
    )
    signature_note: str | None = Field(
        default=None, description="Stated when a role is short of signatures"
    )
    delegates_to: list[str] = Field(default_factory=list)
    artifacts: list[ArtifactSummary] = Field(default_factory=list)
    raw_url: str = Field(
        default="",
        description=(
            "Where to read the bytes this role was verified from, served by "
            "this service, and never linked to the storage behind it"
        ),
    )
