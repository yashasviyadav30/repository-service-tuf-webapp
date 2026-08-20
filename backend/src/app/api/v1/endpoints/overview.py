# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""The whole repository in one answer: roles, their condition, the tree."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1 import errors
from app.api.v1.schemas.overview import OverviewResponse
from app.client.error import MetadataUnavailableError, TrustAnchorMissingError
from app.services.metadata_service import (
    MetadataService,
    get_metadata_service,
)

router = APIRouter(tags=["metadata"])


@router.get(
    "/overview",
    response_model=OverviewResponse,
    responses=errors.REPOSITORY,
    summary="Describe the repository: its roles, their state, and the tree",
)
async def get_overview(
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
        return await service.get_overview(refresh=refresh)
    except TrustAnchorMissingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MetadataUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
