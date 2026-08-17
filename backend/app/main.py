# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Application entry point.

Run it with ``uvicorn app.main:app --reload``.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import cors_origins, get_settings
from app.handlers import health, overview, status
from app.middleware.logging import RequestLogMiddleware

TITLE = "Repository Service for TUF Webapp"
DESCRIPTION = "Read-only web view of a TUF repository managed by RSTUF"


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Read the settings before the first request arrives.

    A server whose startup raised exits rather than serving. Left until the
    first request, a missing value would pass every health check and fail
    everything else, which reads as a broken repository rather than a
    broken deployment.
    """
    get_settings()
    yield


def create_app() -> FastAPI:
    """Assemble the application, so a test can build a separate one."""
    # uvicorn configures its own loggers and leaves the root one alone, so a
    # record from app.* reaches no handler and is dropped. Without this the
    # request log runs and prints nothing.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    # No version: FastAPI already defaults to 0.1.0, and a second copy
    # beside pyproject.toml would drift from it.
    application = FastAPI(
        title=TITLE,
        description=DESCRIPTION,
        lifespan=lifespan,
    )

    application.add_middleware(RequestLogMiddleware)

    # Named origins only, and no credentials across them. It is that
    # pairing that would let another site act as a visitor.
    origins = cors_origins()
    if origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=["GET"],
            allow_headers=["*"],
        )

    application.include_router(health.router)
    application.include_router(overview.router)
    application.include_router(status.router)

    return application


app = create_app()
