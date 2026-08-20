# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""How root reached the version in force today."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1 import errors
from app.api.v1.schemas.roots import RootsResponse
from app.client.error import MetadataUnavailableError, TrustAnchorMissingError
from app.core.constants import DEFAULT_HISTORY, MAX_HISTORY
from app.services.metadata_service import (
    MetadataService,
    get_metadata_service,
)

router = APIRouter(tags=["metadata"])


@router.get(
    "/roots",
    response_model=RootsResponse,
    responses=errors.REPOSITORY,
)
async def get_roots(
    depth: int = Query(
        default=DEFAULT_HISTORY,
        ge=1,
        le=MAX_HISTORY,
        description="How many versions back to walk, counting from the "
        "current one. Not an offset: the walk always starts at the root "
        "the client verified",
    ),
    service: MetadataService = Depends(get_metadata_service),
) -> RootsResponse:
    """Show how root reached its current version.

    Each step is checked against the rule the specification sets for a
    rotation, so a version that cannot be tied to the one before it is
    reported as exactly that.
    """
    try:
        return await service.get_root_history(depth=depth)
    except TrustAnchorMissingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MetadataUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
