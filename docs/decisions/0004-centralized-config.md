# 0004 — Centralize config with pydantic-settings

**Status:** Accepted
**Date:** 2026-08-14
**Commit:** `f7d63be`

## Who

Me, second step of the foundation-cleanup phase.

## What

Replaced scattered `os.getenv(...)` calls (four different files, each redeclaring its own
default, each calling `load_dotenv()` independently) with a single `Settings` class
(`pydantic-settings`) in `src/app/core/config.py`, loaded once and cached via `get_settings()`.

## When

2026-08-14, commit `f7d63be`.

## Where

New: `src/app/core/config.py`. Updated to consume it: `main.py`, `db/engine.py`, `db/db.py`,
`api/routes/links.py` (dropped its now-redundant `load_dotenv()`).

## Why

Before this, there was no single place that knew the full set of config the app depends on, and
no validation that a value was well-formed before the app started using it. Each of
`os.getenv("DEV_DATABASE_URL")`, `os.getenv("DEV_ENV", "False") == "True"` etc. was a
hand-rolled, unvalidated parse repeated with slightly different defaults in different files — the
kind of duplication where one file's default silently drifts from another's over time.

## How

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    dev_database_url: str | None = None
    dev_env: bool = False
    api_version: str = "v1"
    # (grew over subsequent decisions: log_to_file, log_dir, run_migrations_on_startup,
    #  db_pool_size, db_max_overflow, db_pool_recycle_seconds, db_connect_max_attempts,
    #  db_connect_retry_base_delay_seconds — see 0005, 0006, 0007, 0009)

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
```

Field names deliberately map 1:1 to the existing env var names — this was a **pure refactor of
where config is read from**, not a change to what's configured. `DEV_DATABASE_URL` becoming
`DATABASE_URL` (the Render/Postgres-native name) was explicitly deferred rather than bundled in,
so this commit's diff is reviewable as "moved, not changed."

`pydantic-settings` reads `.env` itself, so the standalone `load_dotenv()` calls scattered across
four files were removed as a side effect.

## Alternatives considered

A plain dataclass with manual `os.getenv` parsing inside `__init__` was the "do it myself"
alternative — rejected because `pydantic-settings` gives type coercion and validation for free
(a malformed `DB_POOL_SIZE=notanumber` fails loudly at startup instead of producing a confusing
`TypeError` three layers deep at request time).

## Consequences

- One object to extend every time a new decision needs a new tunable (and nearly every subsequent
  decision in this log did — see the field list above).
- `get_settings()` is `@lru_cache`d, same pattern as `create_db_engine()` — settings are read
  once per process, which matters for the test-isolation pattern in
  [`0006`](0006-alembic-migrations.md) and [`0008`](0008-healthz-liveness-readiness-split.md):
  env vars have to be set *before* the first import that triggers `get_settings()`.
