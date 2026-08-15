from __future__ import annotations

import os
from functools import lru_cache

from app.db.db import db_engine_factory
from app.db.db_exceptions import DBEngineError
from dotenv import load_dotenv
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

load_dotenv()


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
    # Database Config:
    dev_database_url = os.getenv("DEV_DATABASE_URL")
    DATABASE_URL: str = dev_database_url if dev_database_url else "sqlite:///:memory:"

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
        dev_mode=os.getenv("DEV_ENV", "False") == "True",
        **engine_kwargs,
    )

    if not db_engine or not isinstance(db_engine, Engine):
        db_engine_error = {
            "name": "db-error",
            "description": "An error occurred with DB Engine!",
        }
        raise DBEngineError(db_engine_error)

    return db_engine
