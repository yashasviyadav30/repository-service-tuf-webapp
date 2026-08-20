# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""The versioned API, assembled from one router per subject."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    artifacts,
    overview,
    roles,
    roots,
    status,
)

api_v1 = APIRouter(prefix="/api/v1")

api_v1.include_router(artifacts.router)
api_v1.include_router(overview.router)
api_v1.include_router(roles.router)
api_v1.include_router(roots.router)
api_v1.include_router(status.router)
