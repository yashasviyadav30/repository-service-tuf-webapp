# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Runtime configuration, read from ``RSTUF_`` environment variables."""

import os
from functools import lru_cache

from dynaconf import Dynaconf, Validator


@lru_cache
def get_settings() -> Dynaconf:
    """Return the settings, reading the environment only on first call.

    Raises when ``RSTUF_METADATA_URL`` is unset, so a deployment missing it
    fails at startup rather than answering every health check and failing
    every real request.
    """
    settings = Dynaconf(envvar_prefix="RSTUF")
    settings.validators.register(Validator("METADATA_URL", must_exist=True))
    settings.validators.validate()
    return settings


def cors_origins() -> list[str]:
    """Origins allowed to call this API from a browser, comma separated.

    Read from the environment directly because middleware is attached while
    the application is being built, before the settings are validated.
    """
    raw = os.environ.get("RSTUF_CORS_ORIGINS", "")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]
