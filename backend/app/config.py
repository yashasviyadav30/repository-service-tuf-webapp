# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Runtime configuration, read from environment variables.

Nothing is hardcoded, so a single container image serves any deployment.
Each setting is prefixed with ``RSTUF_``: the field ``metadata_url`` comes
from ``RSTUF_METADATA_URL``.
"""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings, read once while the server starts."""

    model_config = SettingsConfigDict(env_prefix="RSTUF_")

    metadata_url: str
    """Base URL of the signed TUF metadata. Required."""

    trusted_root: str | None = None
    """Base64 trust anchor, following the RSTUF client convention.

    Holds either the root metadata itself or a URL pointing at it. Without
    one nothing can be checked, and the service says so rather than showing
    metadata it did not verify.
    """

    api_url: str | None = None
    """Base URL of the RSTUF API. Unset hides the repository status panel."""

    cache_ttl_seconds: int = 30
    """How long a built response stays reusable."""

    request_timeout_seconds: float = 10.0
    """Ceiling on the requests this code makes itself.

    The metadata chain is fetched by python-tuf, which times out on its own.
    """


@lru_cache
def get_settings() -> Settings:
    """Return the settings, reading the environment only on first call."""
    return Settings()


def cors_origins() -> list[str]:
    """Origins allowed to call this API from a browser, comma separated.

    The interface is its own application on its own port, which a browser
    treats as another site. Its dev server can forward /api here and avoid
    the question; where it does not, the port it serves from goes here.
    Empty by default, because an origin nobody named is not allowed.

    Read from the environment rather than through ``Settings``, because
    middleware is attached while the application is being built, before
    anything has decided whether this process is a server or a schema dump.
    """
    raw = os.environ.get("RSTUF_CORS_ORIGINS", "")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]
