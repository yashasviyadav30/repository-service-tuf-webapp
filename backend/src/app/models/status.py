# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""What the RSTUF API reported, before it becomes a response."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.enums import RepositoryState


@dataclass
class RepositoryStatus:
    """What the RSTUF API says about the repository right now."""

    available: bool = False
    state: RepositoryState = RepositoryState.NOT_INITIALISED
    bootstrap: str | None = None
    awaiting_signatures: list[str] = field(default_factory=list)
    message: str | None = None
