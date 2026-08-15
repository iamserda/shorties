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

    engine_kwargs = {}
    if DATABASE_URL in ("sqlite://", "sqlite:///:memory:") or (
        DATABASE_URL.startswith("sqlite") and ":memory:" in DATABASE_URL
    ):
        # In-memory sqlite is per-connection by default, so without a
        # shared StaticPool, each new connection sees an empty database.
        engine_kwargs = {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
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
