# Shorties

A URL shortener built with FastAPI + SQLModel. Early-stage, actively evolving — this README is meant to be kept up to date as the app changes, not written once and forgotten.

## Overview

Shorties transforms long URLs into short, shareable keys. It's a personal/learning project coming out of Inwood, NYC, currently in active early development — expect the API, schema, and infra to keep changing.

> This README tracks reality as of the current commit. If a section here doesn't match the code, the code wins — please open a PR to fix the docs.

## What's here today

- FastAPI app (`src/app/main.py`) with a single versioned router (`/v1`)
- SQLModel/SQLAlchemy models backed by SQLite by default (`DEV_DATABASE_URL` in `.env`)
- Alphanumeric key generation using `secrets.choice` (`src/app/alnumgen.py`), key length configurable via `KEY_MIN`/`KEY_MAX`
- Basic CRUD-ish endpoints:
  - `GET /v1/healthz/` — liveness + DB connectivity check
  - `GET /v1/links/` — list stored shorti links (max 20 per page)
  - `GET /v1/redirect/{shorti_key}` — redirect to the stored URL
  - `POST /v1/create/` — create a new shorti link
  - `DELETE /v1/delete/{shorti_key}` — delete a shorti link by key
- File-based logging to `src/app/logs/main.log`
- Poetry-managed deps, `ruff` + `mypy` + `pre-commit`, pytest suite, GitHub Actions CI (lint, format check, tests on 3.11/3.14)
- `Dockerfile` and `docker-compose.yaml` exist but are placeholders/WIP, not yet a working deploy path

## What's planned — production readiness

Roughly in priority order, not committed to any timeline:

- [ ] Fix URL validation on submission and add safeguards against open-redirect abuse
- [ ] Auth/rate-limiting on write endpoints (`create`, `delete`) — currently unauthenticated and unthrottled
- [ ] Fail-fast startup config validation (e.g. refuse to boot without a real DB URL outside dev)
- [ ] Move default persistence off in-memory/SQLite dev DB to Postgres for non-local environments
- [ ] Flesh out `core/config.py`, `db/session.py`, `api/routes/health.py` (currently empty stubs) or remove them
- [ ] Structured request logging / observability (metrics, tracing) beyond a flat log file
- [ ] Make `make precommit-all` run the full pytest suite; only print the pytest success message after the tests actually pass
- [ ] Pagination cursoring for `/links/` beyond the current fixed 20-item cap
- [ ] Real Docker/Compose setup for local + prod parity
- [ ] API versioning that actually works end-to-end (multiple concurrent versions, not just `/v1`)
- [ ] Click/visit analytics per shorti link

## Aspirational

Longer-term, loosely-held ideas — not commitments, and the shape of these will change:

- Custom/vanity keys and branded short domains
- Link expiration and scheduled takedown
- A minimal web UI for creating and managing links without hitting the API directly

## Getting Started

## Quickstart

### Local (Poetry)

```bash
git clone git@github.com:iamserda/shorties.git
cd shorties

cp .env.example .env
make install # poetry install
# run the app (dev)
make run # poetry run python src/app/main.py
# quality checks
make lint # poetry run pre-commit run ruff-check
make format # poetry run pre-commit run ruff-format
make typecheck # poetry run pre-commit run -v mypy .
make test # poetry run pytest -q
# before every commit, devs should:
make precommit # running make recipes: lint, format, test, typecheck, and poetry run precommit run
# or
make precommit-all # running make recipes: lint, format, test, typecheck, and poetry run precommit run --all-files
```

### With more details:
To get up and running with Shorties, follow these steps:

1. **Clone the repository:**

   ```sh
   git clone git@github.com:iamserda/shorties.git
   cd shorties
   ```

2. **Install Poetry:**
   - **Linux/Windows(via Linux Subsystem):**
     ```sh
     sudo apt install poetry
     ```
   - **macOS:**
     ```sh
     brew install pipx
     pipx install poetry
     ```

3. **Activate virtual-env, install project dependencies(incl. dev-deps):**
   Ensure you are in the project root (where `pyproject.toml` is located):

   ```sh
   eval $(poetry env activate)
   poetry install
   ```

4. **Run the application:**
   Further instructions for running the service will be provided in future updates as config is subject to change to be more autonomous for deployment.
   For now, we will use:

   ```bash
   make run # poetry run python src/app/main.py
   ```

## Contributing

Contributions are welcome and encouraged. If you have ideas for the upcoming twist, architectural improvements, or feature requests, please open an issue or submit a pull request. All contributions should adhere to clean code principles and include relevant documentation and tests where applicable.

## License

This project is licensed under the MIT License.
