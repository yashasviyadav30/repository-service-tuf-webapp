# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Liveness, and nothing else."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz", tags=["ops"])
def healthz() -> dict[str, str]:
    """Report that the process is alive.

    It says nothing about the repository. A repository in trouble is what
    this service exists to show, so it must never be what takes the pod
    down. The path sits outside anything versioned, because a probe is
    configured once when a deployment is created and should not have to
    move again.
    """
    return {"status": "ok"}
