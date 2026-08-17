# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""What the repository vouches for, bin by bin."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.client.tuf_client import MetadataUnavailableError
from app.dto.schemas import ArtifactBinsResponse, ArtifactsResponse
from app.handlers import errors
from app.services.metadata_service import (
    MetadataService,
    TrustAnchorMissingError,
    get_metadata_service,
)

router = APIRouter(prefix="/api/v1", tags=["metadata"])

# A role name arrives in a query string and is used to pick out entries by
# role, so it is constrained here and never trusted. Empty means every role,
# which is why the name and the absence of one share one pattern.
ROLE_NAME_OR_EMPTY = r"^$|^[A-Za-z0-9._-]{1,128}$"


@router.get(
    "/artifacts/bins",
    response_model=ArtifactBinsResponse,
    responses=errors.REPOSITORY,
)
async def artifact_bins(
    service: MetadataService = Depends(get_metadata_service),
) -> ArtifactBinsResponse:
    """Name every role holding artifacts, with how many it holds.

    Asked for before the artifacts themselves, so a repository split across
    256 bins opens as a list of counts. The alternative is a table of every
    package it has ever carried.
    """
    try:
        return await service.artifact_bins()
    except TrustAnchorMissingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MetadataUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get(
    "/artifacts",
    response_model=ArtifactsResponse,
    responses=errors.REPOSITORY,
)
async def artifacts(
    search: str = Query(default="", max_length=256),
    role: str = Query(
        default="",
        pattern=ROLE_NAME_OR_EMPTY,
        description="Limit to one role. Omit to search across all of them",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    service: MetadataService = Depends(get_metadata_service),
) -> ArtifactsResponse:
    """List the artifacts the repository vouches for.

    Names, sizes and hashes only. The visualizer never serves the files
    themselves, and never claims one is safe to install.
    """
    try:
        return await service.artifacts(
            search=search, role=role, page=page, page_size=page_size
        )
    except TrustAnchorMissingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MetadataUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
