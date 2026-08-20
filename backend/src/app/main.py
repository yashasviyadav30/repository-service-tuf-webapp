# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Application entry point."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.api.router import api_v1
from app.config import cors_origins, get_settings
from app.core.constants import TITLE
from app.core.logging import RequestLogMiddleware

# uvicorn configures its own loggers and leaves the root one alone, so a
# record from app.* would otherwise reach no handler and be dropped.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Read the settings before the first request arrives."""
    get_settings()
    logger.info("The application started successfully.")
    yield


def create_app() -> FastAPI:
    """Assemble the application, so a test can build a separate one."""
    application = FastAPI(title=TITLE, lifespan=lifespan)

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
    application.include_router(api_v1)

    return application


app = create_app()
