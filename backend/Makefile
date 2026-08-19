# Short names for long commands. See README.md for what each one is for.

.PHONY: all setup precommit run-dev tests tests-docker lint reformat

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

run-dev:
	uv run uvicorn app.main:app --reload --port 8080

reformat:
	uv run black src/app tests
	uv run isort src/app tests

tests:
	uv run pytest

# The venv is built at /tmp so the one on the host, which was built for a
# different platform, is left alone.
tests-docker:
	docker run --rm -v "$(CURDIR):/w" -w /w \
		-e UV_PROJECT_ENVIRONMENT=/tmp/venv python:3.13-slim \
		bash -c "pip install --quiet --no-cache-dir uv \
		&& uv sync --locked --quiet \
		&& uv run pytest -q"

lint:
	uv run flake8 src/app tests
	uv run black --check --diff src/app tests
	uv run isort --check --diff src/app tests
	uv run bandit -q -r src/app
