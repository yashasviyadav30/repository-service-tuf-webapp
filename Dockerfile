# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

# Build from the repository root:
#
#     docker build -t rstuf-webapp .

# --- dependencies -----------------------------------------------------------
#
# Resolved in a throwaway stage so neither uv nor a build cache reaches the
# image that ships. Versions come from uv.lock and are installed with their
# hashes, so a build either produces the audited dependency set or fails.

FROM python:3.13-slim AS dependencies

RUN pip install --no-cache-dir uv==0.12.4

WORKDIR /build
COPY backend/pyproject.toml backend/uv.lock ./

RUN uv export --locked --no-dev --no-emit-project > requirements.txt \
    && python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --require-hashes \
       -r requirements.txt

# --- runtime ----------------------------------------------------------------

FROM python:3.13-slim

LABEL org.opencontainers.image.title="RSTUF Webapp" \
      org.opencontainers.image.description="Read-only web view of a TUF \
repository managed by Repository Service for TUF" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/repository-service-tuf/repository-service-tuf-webapp"

COPY --from=dependencies /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# The layout of the source tree is kept, so the working directory matches
# what the tests and the local runner use.
WORKDIR /srv/backend
COPY backend/app ./app

# Nothing here writes to its own files. The one directory the service does
# write is the trust directory under /tmp, which holds what the TUF client
# has verified, so a read-only root filesystem needs /tmp mounted and nothing
# else.
RUN useradd --create-home --uid 1001 webapp \
    && chown -R webapp:webapp /srv
USER webapp

EXPOSE 8000

# For anyone running this outside Kubernetes. A cluster uses the probes in
# the chart instead, and both ask the same endpoint.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request as r; \
r.urlopen('http://127.0.0.1:8000/healthz', timeout=2)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
