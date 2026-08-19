# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Liveness, and nothing else."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz", tags=["ops"])
def get_health() -> dict[str, str]:
    """Report that the process is alive.

    Says nothing about the repository: a repository in trouble is what this
    service exists to show, so it must never be what takes the pod down.
    """
    return {"status": "ok"}
