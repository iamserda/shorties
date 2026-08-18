# Shorties

A URL shortener service built with FastAPI, SQLModel, and Postgres. Create short links, redirect visitors, and track click analytics.

Built from Inwood, NYC ("The Silicon Valley of the northeast! So I have heard!").

- Repo: https://github.com/iamserda/shorties
- Author: [iamserda](https://github.com/iamserda) · [LinkedIn](https://linkedin.com/in/iamserda)

## Features

- Create short links for any URL, with an optional brand label and choice of redirect type (301/302/307)
- Redirect visitors from a short link to its target URL
- Per-link click analytics: hit count, last-accessed time, and recent click history (referrer, user agent)
- Soft-delete links (recoverable, excluded from default listings)
- Liveness (`/healthz/`) and readiness (`/healthz/ready`) endpoints for orchestration/load balancers
- Alembic-managed schema migrations, run automatically on startup
- Postgres in production, with startup connection retry (exponential backoff) for containerized environments where the app can start before the DB is ready

## Tech Stack

- **API**: FastAPI + Uvicorn
- **Data**: SQLModel (SQLAlchemy) over Postgres (via `psycopg`), Alembic for migrations
- **Config**: `pydantic-settings`, reading from `.env`
- **Tooling**: Poetry, Ruff (lint + format), mypy, pytest, pre-commit

## Getting Started (Local Development)

### Prerequisites

- Python >= 3.11
- [Poetry](https://python-poetry.org/)
- Docker (for a local Postgres instance) or your own Postgres connection string

### Quickstart

```bash
git clone git@github.com:iamserda/shorties.git
cd shorties

cp .env.example .env
# then fill in DEV_DATABASE_URL (and friends) in .env — see Configuration below

make install       # poetry install
make run            # poetry run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8001
```

The API will be available at `http://localhost:8001`, with interactive docs at `http://localhost:8001/docs`.

### Detailed setup

1. **Clone the repository:**

   ```sh
   git clone git@github.com:iamserda/shorties.git
   cd shorties
   ```

2. **Install Poetry:**
   - **Linux/WSL:**
     ```sh
     sudo apt install poetry
     ```
   - **macOS:**
     ```sh
     brew install pipx
     pipx install poetry
     ```

3. **Install dependencies** (from the project root, where `pyproject.toml` lives):

   ```sh
   eval $(poetry env activate)
   poetry install
   ```

4. **Configure your environment:**

   ```sh
   cp .env.example .env
   ```

   At minimum, set `DEV_DATABASE_URL` to a Postgres connection string. See [Configuration](#configuration) below for all available settings.

5. **Bring up Postgres** (optional convenience via Docker):

   ```sh
   docker compose up -d postgres
   ```

6. **Run the application:**

   ```sh
   make run
   ```

   Database migrations run automatically on startup (see `run_migrations_on_startup` in Configuration). You can also run them manually:

   ```sh
   make migrate
   ```

### Configuration

Settings are read from `.env` (see `.env.example`) via `src/app/core/config.py`. Key variables:

| Variable | Default | Description |
|---|---|---|
| `DEV_DATABASE_URL` | — | Postgres connection string |
| `DEV_ENV` | `False` | Marks the environment as development |
| `API_VERSION` | `v1` | Prefix applied to all API routes (e.g. `/v1/links`) |
| `LOG_TO_FILE` | `True` | Whether to also write logs to `LOG_DIR` |
| `LOG_DIR` | `logs` | Directory for log files |
| `RUN_MIGRATIONS_ON_STARTUP` | `True` | Run Alembic migrations to `head` when the app starts |
| `DB_POOL_SIZE` | `5` | SQLAlchemy connection pool size |
| `DB_MAX_OVERFLOW` | `10` | Extra connections allowed beyond pool size |
| `DB_POOL_RECYCLE_SECONDS` | `1800` | Recycle idle connections before a managed DB closes them |
| `DB_CONNECT_MAX_ATTEMPTS` | `5` | Startup DB connection retry attempts |
| `DB_CONNECT_RETRY_BASE_DELAY_SECONDS` | `1.0` | Base delay (exponential backoff) between retries |

### Common tasks

```bash
make install          # install dependencies
make run               # run the dev server (reload enabled)
make migrate            # apply Alembic migrations
make makemigrations message="add foo column"   # generate a new migration
make lint                # ruff check
make format              # ruff format
make typecheck            # mypy
make test                  # pytest
make precommit              # lint + format + typecheck + test (staged files)
make precommit-all           # same, but across all files
```

Run `make precommit` before every commit.

## Usage (API Guide)

All routes are prefixed with the configured API version, e.g. `/v1`. Interactive, always-up-to-date docs are served at `/docs` (Swagger UI) and `/redoc`.

### Health checks

| Method | Path | Description |
|---|---|---|
| GET | `/v1/healthz/` | Liveness — is the process up? Does not touch the DB. |
| GET | `/v1/healthz/ready` | Readiness — can this instance serve a DB-backed request? |

### Links

| Method | Path | Description |
|---|---|---|
| GET | `/v1/links/` | List links (paginated via `offset`/`limit`, max 20 per page). Pass `include_deleted=true` to include soft-deleted links. |
| POST | `/v1/links/` | Create a new short link |
| GET | `/v1/links/{shorti_key}` | Get a single link's details |
| PUT | `/v1/links/{shorti_key}` | Update a link's URL, brand, or redirect code |
| DELETE | `/v1/links/{shorti_key}` | Soft-delete a link |
| GET | `/v1/links/{shorti_key}/visit` | Redirect to the link's target URL, recording a click |
| GET | `/v1/links/{shorti_key}/analytics` | Get hit count and recent click history for a link |

### Examples

**Create a short link:**

```bash
curl -X POST http://localhost:8001/v1/links/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/some/very/long/path", "brand": "example", "redirect_code": 302}'
```

```json
{
  "key": "aB3xQ9",
  "url": "https://example.com/some/very/long/path",
  "brand": "example",
  "redirect_code": 302,
  "hit_count": 0,
  "created_at": "2026-08-18T00:00:00Z",
  "updated_at": "2026-08-18T00:00:00Z",
  "last_accessed_at": null
}
```

**Visit / redirect a short link:**

```bash
curl -i http://localhost:8001/v1/links/aB3xQ9/visit
# HTTP/1.1 302 Found
# Location: https://example.com/some/very/long/path
```

**Get analytics for a link:**

```bash
curl http://localhost:8001/v1/links/aB3xQ9/analytics
```

**Update a link:**

```bash
curl -X PUT http://localhost:8001/v1/links/aB3xQ9 \
  -H "Content-Type: application/json" \
  -d '{"brand": "new-brand"}'
```

**Delete (soft-delete) a link:**

```bash
curl -X DELETE http://localhost:8001/v1/links/aB3xQ9
```

## Testing

```bash
make test
```

Tests use an isolated in-memory database and never touch a real configured DB.

## Contributing

Contributions are welcome. Please run `make precommit` before opening a pull request, and include tests for any new behavior.

## License

This project is licensed under the MIT License.
