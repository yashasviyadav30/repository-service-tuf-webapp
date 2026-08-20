# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""What the repository vouches for, bin by bin."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1 import errors
from app.api.v1.schemas.artifacts import (
    ArtifactBinsResponse,
    ArtifactsResponse,
)
from app.client.error import MetadataUnavailableError, TrustAnchorMissingError
from app.core.constants import ROLE_NAME_OR_EMPTY
from app.services.metadata_service import (
    MetadataService,
    get_metadata_service,
)

router = APIRouter(tags=["metadata"])


@router.get(
    "/artifacts/bins",
    response_model=ArtifactBinsResponse,
    responses=errors.REPOSITORY,
)
async def get_artifact_bins(
    service: MetadataService = Depends(get_metadata_service),
) -> ArtifactBinsResponse:
    """Name every role holding artifacts, with how many it holds.

    Asked for before the artifacts themselves, so a repository split across
    256 bins opens as a list of counts. The alternative is a table of every
    package it has ever carried.
    """
    try:
        return await service.get_artifact_bins()
    except TrustAnchorMissingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MetadataUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get(
    "/artifacts",
    response_model=ArtifactsResponse,
    responses=errors.REPOSITORY,
)
async def get_artifacts(
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
        return await service.get_artifacts(
            search=search, role=role, page=page, page_size=page_size
        )
    except TrustAnchorMissingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MetadataUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
