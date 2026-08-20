# Short names for long commands. See README.md for what each one is for.

.PHONY: all setup precommit run-dev tests tests-unit tests-integration \
	tests-docker lint reformat fixtures run-local

all: lint tests

setup:
	@command -v uv >/dev/null 2>&1 || { \
		echo "uv is not installed. Install it with:"; \
		echo "  pip install uv"; \
		echo "or see https://docs.astral.sh/uv/getting-started/installation/"; \
		exit 1; \
	}
	uv sync

precommit:
	uv run pre-commit install
	uv run pre-commit run --all-files

# --app-dir puts src on the import path. Only pytest reads the pythonpath in
# pyproject.toml, so every other entry point has to say where the app lives.
run-dev:
	uv run uvicorn app.main:app --reload --port 8080 --app-dir src

reformat:
	uv run black src/app tests scripts
	uv run isort src/app tests scripts

tests:
	uv run pytest

tests-unit:
	uv run pytest tests/unit

tests-integration:
	uv run pytest tests/integration

# python-tuf caches its trust anchor behind a symbolic link, which Windows
# refuses without Developer Mode, so the integration tests skip themselves
# there. This runs everything on Linux. The venv is built at /tmp so the one
# on the host, which was built for a different platform, is left alone.
tests-docker:
	docker run --rm -v "$(CURDIR):/w" -w /w \
		-e UV_PROJECT_ENVIRONMENT=/tmp/venv python:3.13-slim \
		bash -c "pip install --quiet --no-cache-dir uv \
		&& uv sync --locked --quiet \
		&& uv run pytest -q"

fixtures:
	uv run python scripts/gen_fixture.py

run-local:
	./scripts/run_local.sh

lint:
	uv run flake8 src/app tests scripts
	uv run black --check --diff src/app tests scripts
	uv run isort --check --diff src/app tests scripts
	uv run bandit -q -r src/app
