# RSTUF webapp backend

A read-only HTTP view of a TUF repository managed by RSTUF. It fetches the
signed metadata, verifies it with `python-tuf`, and answers with small JSON.
It stores nothing and changes nothing.

## Requirements

- Python 3.13
- [uv](https://docs.astral.sh/uv/getting-started/installation/), which
  installs the dependencies and runs every command:

  ```
  pip install uv
  ```

- Docker, for `make tests-docker` only.

## Install

```
cd backend
make setup
```

## Run

```
RSTUF_METADATA_URL=https://example.org/metadata/ make run-dev
```

The API answers on <http://localhost:8080>. The OpenAPI schema and the
interactive docs are at <http://localhost:8080/docs>, which is what the
frontend generates its types from.

Startup fails if `RSTUF_METADATA_URL` is unset, so a misconfigured
deployment exits rather than passing health checks and failing every real
request.

## Settings

Read from the environment with a `RSTUF_` prefix, via Dynaconf.

| Variable | Required | What it does |
|---|---|---|
| `RSTUF_METADATA_URL` | yes | Base URL of the signed TUF metadata |
| `RSTUF_CORS_ORIGINS` | no | Comma-separated origins allowed to call this API from a browser. Empty by default, so nothing is allowed |

The frontend dev server runs on its own port, which a browser treats as
another site. Where it does not forward `/api` to this service, name its
origin in `RSTUF_CORS_ORIGINS`.

## Tests and linting

```
make tests          # unit tests
make tests-docker   # everything, on Linux, where nothing skips
make lint           # flake8, black, isort, bandit
make reformat       # black and isort, in place
```

On Windows some tests skip: `python-tuf` caches its trust anchor behind a
symbolic link, which the platform refuses without Developer Mode. A green
run there proves less than it looks, so `make tests-docker` is the check
that counts.

## Pre-commit

```
make precommit
```

That runs `pre-commit install`, which writes the git hook, and then runs
every hook once over the whole tree. After it, each `git commit` runs
flake8, black, isort and bandit on what is staged.

## Layout

```
src/app/
├── main.py       assembles the application
├── config.py     settings, read from RSTUF_* variables
├── api/          one module per subject
└── core/         constants, and request logging
tests/
└── unit/
```
