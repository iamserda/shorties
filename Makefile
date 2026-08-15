.PHONY: help install test lint fmt format typecheck precommit precommit-all migrate makemigrations

help:
	@echo "Targets: help install test lint fmt format typecheck precommit precommit-all migrate makemigrations"

activate:
	@echo 'To activate virtual env, run the following in your shell:'
	@echo 'eval "$$(make -s env)"'

venv:
	poetry env activate

install:
	poetry install

fmt format:
	poetry run pre-commit run ruff-format

lint:
	poetry run pre-commit run ruff-check

run:
	poetry run uvicorn src.app.main:app --reload --reload-dir=. --host 0.0.0.0 --port 8001 --log-level debug

migrate:
	poetry run alembic upgrade head

# Usage: make makemigrations message="add foo column"
makemigrations:
	poetry run alembic revision --autogenerate -m "$(message)"

test:
	poetry run pytest -q

typecheck:
	poetry run pre-commit run -v mypy

precommit: lint format typecheck test
	@echo "✅ ruff-lint checks passed"
	@echo "✅ ruff-format checks passed"
	@echo "✅ mypy-typecheck checks passed"
	@echo "✅ pytest-test checks passed"
	@echo "✅ precommit(--stage-files-only) checks passed"

precommit-all:
	poetry run pre-commit run --all-files
	@echo "✅ ruff-lint checks passed"
	@echo "✅ ruff-format checks passed"
	@echo "✅ mypy-typecheck checks passed"
	@echo "✅ pytest-test checks passed"
	@echo "✅ precommit(--stage-files-only) checks passed"
