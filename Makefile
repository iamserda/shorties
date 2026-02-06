.PHONY: help install test lint fmt format typecheck ci

help:
	@echo "Targets: install, test, lint, fmt, typecheck, ci, activate"

activate:
	@echo 'To activate virtual env, run the following in your shell:'
	@echo 'eval "$$(make -s activate_venv)"'

activate_venv:
	poetry env activate

install:
	poetry install

ruff:
	poetry run pre-commit run ruff

fmt format:
	poetry run pre-commit run ruff-format

lint:
	poetry run pre-commit run ruff-check

run:
	poetry run python src/app/main.py

test:
	poetry run pytest -q

typecheck:
	poetry run mypy .

precommit: lint format typecheck test
	poetry run pre-commit run

precommit-all: lint format typecheck test
	poetry run pre-commit run --all-files
