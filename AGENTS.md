# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## What this is

Shorties is an early-stage, actively-changing FastAPI + SQLModel URL shortener (personal/learning project). Expect API, schema, and infra to keep shifting — `README.md` is meant to track current reality, and `TODO.md` is the maintained, prioritized list of known bugs and planned work. **Check `TODO.md` before treating something as a newly-discovered issue** — most rough edges in `api/routes/links.py`, `db/`, and the Makefile are already tracked there with a decision on priority.

## Working with this repo

- **This is a learning project the user is building to understand front-to-back — lean toward reviewing, diagnosing, and explaining over writing large amounts of code unprompted.** A prior branch (`dev0`, since abandoned) grew a lot of AI-authored code (Postgres migration, Alembic, Docker, structured logging, etc.) and the user explicitly reconsidered it because they didn't feel ownership or understanding of it, even with documentation. The current branch was started fresh with the user driving implementation more directly. Don't reintroduce that dev0-style scope (Postgres/Docker/Alembic-in-main/pydantic-settings) speculatively — it isn't part of this branch's actual code, and taking over the design again would repeat the same mistake.
- **Prove correctness, don't assert it.** Before claiming a fix or feature works, actually run the relevant tests (`make test`, or a scoped `pytest` invocation) and show the result — don't report success from reading the code alone.
- **When something is broken (e.g. after a merge or rebase), diagnose and recommend before touching code.** Identify root cause, distinguish it from cosmetic/secondary issues, and get explicit go-ahead on the fix before editing — especially for anything touching git history or already-merged commits.
- Prefer small, individually testable, individually revertible commits over large batched changes, particularly when working through a multi-step initiative (e.g. the TODO.md checklist) — each step should leave the app and test suite in a known-good state.
- File-based logging (`src/app/logs/main.log`) is a deliberate choice, not an oversight — logs are meant to be reviewable locally after the fact. If logging is reworked later (e.g. to also log to stdout for containers), keep the file output rather than replacing it.

## Commands

```bash
make install        # poetry install
make run             # poetry run python src/app/main.py
make lint            # poetry run pre-commit run ruff-check
make format           # poetry run pre-commit run ruff-format
make typecheck       # poetry run pre-commit run -v mypy
make test            # poetry run pytest -q
make precommit       # lint + format + typecheck + test, then pre-commit (staged files only)
make precommit-all   # same as above, then pre-commit --all-files
```

- Single test: `poetry run pytest tests/db_test.py::test_db_engine_factory_creates_engine_for_valid_url -q`
- Tests set `pythonpath = ["src"]` in `pyproject.toml`, so `app.*` imports resolve without installing the package.
- CI (`.github/workflows/ci.yml`) runs on Python 3.11 and 3.14: `ruff check .`, `ruff format --check .`, `pytest -q`. It does **not** set `DEV_DATABASE_URL`, which is a known gap tracked in `TODO.md`.
- `make precommit-all`'s pytest step currently prints success regardless of test outcome — also tracked in `TODO.md`; don't rely on its output alone to confirm tests passed, check `make test` directly.

## Architecture

**Request flow**: `main.py` loads `.env`, configures file logging (`src/app/logs/main.log`), builds the SQLModel engine, and creates tables — all at **module import time**, not inside an app lifecycle hook (a known issue: importing `app.main` for tests requires overriding the engine dependency rather than relying on lifespan events). It mounts one `APIRouter` under `/{api_version}`, where `api_version` comes from the `API_VERSION` env var but is only ever meaningfully `v1` — `links.py` and `health.py` are the only route modules, so multi-version support advertised by the `v1`–`v5` allow-list doesn't yet exist end-to-end.

**DB layer** (`src/app/db/`):
- `db.py` — `db_engine_factory(db_url, dev_mode)` builds the SQLAlchemy engine; raises typed exceptions (below) that get converted to `HTTPException`s. Also has a `create_dev_db()` script entry point for bootstrapping the SQLite dev DB (`python -m app.db.db`), separate from the app's own runtime table creation.
- `session.py` — `get_db_url(selected_db)` reads the named env var (default `DEV_DATABASE_URL`); `get_db_engine` and `get_session` are the FastAPI `Depends(...)` providers routes use for DB access. Route handlers depend on `get_db_engine` directly and open their own `Session(...)` rather than using `get_session`, except `health.py`, which uses `get_session` — the two patterns coexist.
- `db_exceptions.py` — a custom exception hierarchy (`DatabaseError`, `DbUrlInvalidError`, `EmptyDatabaseError`, `DBEngineError`, `DBSessionError`) that all extend `sqlalchemy.exc.SQLAlchemyError`, not a plain `Exception` base — catch/construct accordingly.
- `models/models.py` — single `ShortiLink` SQLModel table (`shorti_key`, `shorti_url`, `brand`).
- Tests never point at the real configured DB: they build an isolated in-memory `sqlite://` engine (`StaticPool`, `check_same_thread=False`) and override the `get_db_engine` FastAPI dependency via `app.dependency_overrides` (see `tests/app_main_test.py`). Follow this pattern for any new DB-touching test.

**Schemas**: `schemas/schemas.py` holds the Pydantic request/response models (`NewUrlSubmissionModel`, `GetUrlResponseModel`, etc.) actually in use. `schemas/links.py` and `core/config.py` are empty stubs — `TODO.md` calls out finishing or removing them; don't assume they contain logic.

**Key generation**: `alnumgen.py` generates the short key via `secrets.choice` over a length range from `constants.py` (`KEY_MIN`/`KEY_MAX`). It also defines a `test_alnum_generator()` function invoked only via its own `__main__` block — it is not part of the `tests/` suite despite the name; the actual pytest coverage is `tests/alnumgen_test.py`.

**Alembic**: an `alembic/` directory exists locally but is not tracked in git and has no `alembic.ini` — migrations are not yet a working part of this project's workflow (schema changes currently happen via `SQLModel.metadata.create_all()`).

## Conventions

- Every module is expected to start with `from __future__ import annotations` — the `reorder-python-imports` pre-commit hook inserts this and reorders imports automatically; don't hand-order imports against what that hook would produce.
- `ruff.toml`: line length 88, double quotes, `py311` target. `mypy` runs with `--check-untyped-defs`.
- Logging is per-module (`logging.getLogger(__name__)`, mostly), writing to `src/app/logs/main.log`; there's no centralized logging config beyond what `main.py` sets up at import time.
- `engineering_notes.md` documents a standing rule for this repo: if a tooling problem (not product code) takes more than ~25 minutes to resolve, it gets parked as a written note (what was attempted, expected vs. actual, smallest repro) instead of continuing to sink time into it during feature work.
