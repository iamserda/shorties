.PHONY: help install test lint fmt format typecheck precommit precommit-all

help:
	@echo "Targets: install, test, lint, fmt, typecheck, ci, activate"

activate:
	@echo 'To activate virtual env, run the following in your shell:'
	@echo 'eval "$$(make -s activate_venv)"'

activate_venv:
	poetry env activate

install:
	poetry install

fmt format:
	poetry run pre-commit run ruff-format

lint:
	poetry run pre-commit run ruff-check

run:
	poetry run python src/app/main.py

test:
	poetry run pytest -q

typecheck:
	poetry run pre-commit run -v mypy

precommit: lint format typecheck test
	@echo "precommit checks passed"

precommit-all: lint format typecheck test
	poetry run pre-commit run --all-files

# Docker
up:
	docker compose up

down:
	docker compose down
