# Short names for long commands. `make help` prints them all.

.PHONY: all setup precommit run-dev tests tests-docker lint reformat help

all: help

setup:  ## Install the backend's dependencies
	uv sync

precommit:  ## Install and run the pre-commit hooks
	uv run pre-commit install
	uv run pre-commit run --all-files

run-dev:  ## Run the service against a repository named in the environment
	uv run uvicorn app.main:app --reload

reformat:  ## Reformat code with black and isort
	uv run black app tests
	uv run isort app tests

tests:  ## Run all tests
	uv run pytest

tests-docker:  ## Run all tests on Linux, where nothing skips
	docker run --rm -v "$(CURDIR):/w" -w /w python:3.13-slim \
		bash -c "pip install --quiet --no-cache-dir pipenv \
		&& pipenv install --dev --deploy --system --quiet \
		&& pytest -q"

lint:  ## Run the linters CI runs, in the order it runs them
	uv run flake8 app tests
	uv run black --check --diff app tests
	uv run isort --check --diff app tests
	uv run bandit -q -r app

help:  ## Show this message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-14s\033[0m %s\n", $$1, $$2}'
