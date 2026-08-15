from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.db.db import db_engine_factory
from app.db.db_exceptions import DBEngineError
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool


@lru_cache(maxsize=1)
def create_db_engine() -> Engine:
    """
    Get the database engine for interacting with the database.

    Cached so every call within the process returns the same Engine
    instance, regardless of whether it's called directly or resolved
    through FastAPI's dependency injection.

    Returns:
        Engine: A SQLAlchemy Engine object for database operations.
    """
    settings = get_settings()
    DATABASE_URL: str = settings.dev_database_url or "sqlite:///:memory:"

    is_memory_sqlite = DATABASE_URL in ("sqlite://", "sqlite:///:memory:") or (
        DATABASE_URL.startswith("sqlite") and ":memory:" in DATABASE_URL
    )
    is_sqlite = DATABASE_URL.startswith("sqlite")

    if is_memory_sqlite:
        # In-memory sqlite is per-connection by default, so without a
        # shared StaticPool, each new connection sees an empty database.
        engine_kwargs = {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }
    elif is_sqlite:
        # A sqlite file doesn't need pool tuning — there's no remote
        # server to time out or lose a stale connection to — but
        # pre-ping is cheap and harmless everywhere.
        engine_kwargs = {"pool_pre_ping": True}
    else:
        # A real server (Postgres) benefits from an actual bounded pool:
        # pool_pre_ping catches a connection the server already dropped
        # before it surfaces as a request failure, and pool_recycle
        # avoids handing out a connection older than what a managed DB
        # (e.g. Render's Postgres) will silently close server-side.
        engine_kwargs = {
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
            "pool_recycle": settings.db_pool_recycle_seconds,
            "pool_pre_ping": True,
        }

    db_engine = db_engine_factory(
        db_url=DATABASE_URL,
        dev_mode=settings.dev_env,
        **engine_kwargs,
    )

    if not db_engine or not isinstance(db_engine, Engine):
        db_engine_error = {
            "name": "db-error",
            "description": "An error occurred with DB Engine!",
        }
        raise DBEngineError(db_engine_error)

    return db_engine
