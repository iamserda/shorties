from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """Single source of truth for environment configuration.

    Reads from a .env file (if present) and process env vars, with
    process env vars taking precedence. Field names map to the existing
    env var names so this is a pure refactor of where config is read
    from, not a change to what's configured — DEV_DATABASE_URL becoming
    DATABASE_URL is a deliberate later step (Render/Postgres rollout),
    not bundled in here.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    dev_database_url: str | None = None
    dev_env: bool = False
    api_version: str = "v1"

    # Logging
    log_to_file: bool = True
    log_dir: str = "logs"

    # Migrations
    run_migrations_on_startup: bool = True

    # Connection pool (applies to non-sqlite-memory engines, e.g. Postgres)
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_recycle_seconds: int = (
        1800  # recycle idle connections before a managed DB closes them server-side
    )

    # Startup connection retry (e.g. compose: app container starts before
    # Postgres finishes accepting connections)
    db_connect_max_attempts: int = 5
    db_connect_retry_base_delay_seconds: float = 1.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
