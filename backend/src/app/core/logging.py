# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""One line per request: method, path, status and duration."""

import logging
import time

from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Log the method, path, status and duration of each request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        started = time.perf_counter()
        # A handler that raises is the request an operator most wants to
        # find, so the line is written on the way out either way. The
        # traceback is uvicorn's to print; this records that it happened.
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            logger.info(
                "%s %s -> %d in %.0fms",
                request.method,
                request.url.path,
                status,
                (time.perf_counter() - started) * 1000,
            )
