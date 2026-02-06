.PHONY: help install test lint fmt format typecheck ci

help:
	@echo "Targets: install, test, lint, fmt, typecheck, ci, activate"

activate:
	@echo 'To activate virtual env, run the following in your shell:'
	@echo 'eval "$$(make -s activate_venv)"'

activate_venv:
	poetry env activate

ci: lint typecheck test

fmt format:
	poetry run ruff format

install:
	poetry install

lint:
	poetry run ruff check

ruff:
	poetry run ruff

run:
	poetry run python src/app/main.py

test:
	poetry run pytest -q

typecheck:
	poetry run mypy --pretty --show-error-codes .
