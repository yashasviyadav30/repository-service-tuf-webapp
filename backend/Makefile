# Short names for long commands. `make help` prints them all.

.PHONY: all setup precommit run-dev tests tests-unit \
	tests-integration tests-docker lint reformat fixtures \
	run-local help

all: help

setup:  ## Install the backend's dependencies
	uv sync

precommit:  ## Install and run the pre-commit hooks
	uv run pre-commit install
	uv run pre-commit run --all-files

run-dev:  ## Run the service against a repository named in the environment
	uv run uvicorn app.main:app --reload

reformat:  ## Reformat code with black and isort
	uv run black app tests scripts
	uv run isort app tests scripts

tests:  ## Run all tests
	uv run pytest

tests-unit:  ## Run only the tests that reach nothing outside the process
	uv run pytest tests/unit

tests-integration:  ## Run only the tests driven against a real repository
	uv run pytest tests/integration

# python-tuf caches its trust anchor behind a symbolic link, which Windows
# refuses without Developer Mode, so the integration tests skip themselves
# there. This runs everything on Linux.
tests-docker:  ## Run all tests on Linux, where nothing skips
	docker run --rm -v "$(CURDIR):/w" -w /w python:3.13-slim \
		bash -c "pip install --quiet --no-cache-dir uv \
		&& uv sync --quiet && uv run pytest -q"

fixtures:  ## Generate local TUF repositories for development
	uv run python scripts/gen_fixture.py

run-local:  ## Serve a generated repository and read it
	./scripts/run_local.sh

lint:  ## Run the linters CI runs, in the order it runs them
	uv run flake8 app tests scripts
	uv run black --check --diff app tests scripts
	uv run isort --check --diff app tests scripts
	uv run bandit -q -r app

help:  ## Show this message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-14s\033[0m %s\n", $$1, $$2}'
