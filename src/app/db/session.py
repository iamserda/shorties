from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from app.db.db_exceptions import DBEngineError
from fastapi import Depends
from sqlalchemy.engine import Engine
from sqlmodel import Session


def _get_current_engine() -> Engine:
    # Lazy import to avoid a circular import (app.main imports the routers,
    # which import this module). Reading app.main.db_engine at call time
    # (rather than depending on create_db_engine directly) is what lets
    # tests swap in an isolated engine via `app.main.db_engine`.
    from app import main as main_module

    return main_module.db_engine


def get_db_session(
    db_engine: Annotated[Engine, Depends(_get_current_engine)],
) -> Generator[Session, None, None]:
    """
    Yield a database session for interacting with the database.

    The session stays open for the lifetime of the request and is
    closed automatically by FastAPI once the request finishes.
    """
    if not db_engine or not isinstance(db_engine, Engine):
        db_engine_error = {
            "name": "db-error",
            "description": "An error occurred with DB Engine!",
        }
        raise DBEngineError(db_engine_error)

    with Session(db_engine) as session:
        yield session
