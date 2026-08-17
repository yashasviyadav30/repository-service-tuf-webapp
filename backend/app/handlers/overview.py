# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""The whole repository in one answer: roles, their condition, the tree."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.client.tuf_client import MetadataUnavailableError
from app.dto.schemas import OverviewResponse
from app.handlers import errors
from app.services.metadata_service import (
    MetadataService,
    TrustAnchorMissingError,
    get_metadata_service,
)

router = APIRouter(prefix="/api/v1", tags=["metadata"])


@router.get(
    "/overview",
    response_model=OverviewResponse,
    responses=errors.REPOSITORY,
    summary="Describe the repository: its roles, their state, and the tree",
)
async def overview(
    refresh: bool = Query(
        default=False,
        description="Discard the cached reading and check the repository now",
    ),
    service: MetadataService = Depends(get_metadata_service),
) -> OverviewResponse:
    """Everything the first render needs.

    One request draws the whole screen: every role with its version, expiry
    and signers, the delegated roles named but not fetched, and the edges
    between them.
    """
    try:
        return await service.overview(refresh=refresh)
    except TrustAnchorMissingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MetadataUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
