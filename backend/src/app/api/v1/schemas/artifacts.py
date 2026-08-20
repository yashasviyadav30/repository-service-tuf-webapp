# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""What the artifacts screen receives."""

from pydantic import BaseModel, Field


class ArtifactSummary(BaseModel):
    """One artifact listed by a delegated role."""

    path: str
    length: int
    hashes: dict[str, str] = Field(default_factory=dict)
    role: str = Field(description="The delegated role listing it")


class ArtifactsResponse(BaseModel):
    """A page of artifacts, gathered from delegated roles."""

    total: int
    page: int
    page_size: int
    artifacts: list[ArtifactSummary] = Field(default_factory=list)
    unavailable: list[str] = Field(
        default_factory=list,
        description=(
            "Delegated roles that could not be read. Whatever they list is "
            "missing from this page, and from the total beside it, so the "
            "shortfall is named and does not pass for an empty bin"
        ),
    )


class BinSummary(BaseModel):
    """One role that holds artifacts, and how many it holds."""

    name: str
    count: int
    available: bool = Field(
        default=True,
        description=(
            "False when the role could not be read. Its count is then 0, "
            "which is not the same as the role being empty"
        ),
    )


class ArtifactBinsResponse(BaseModel):
    """Every role holding artifacts, so the browser can open one at a time.

    The interface asks for this before it asks for artifacts, which is what
    keeps a repository of 256 bins from sending 256 bins to draw one screen.
    """

    total: int
    bins: list[BinSummary] = Field(default_factory=list)
