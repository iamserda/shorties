from __future__ import annotations

import logging
import os
from typing import Annotated

from app.db.db import db_engine_factory
from dotenv import load_dotenv
from fastapi import Depends
from fastapi.exceptions import HTTPException
from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

from .db_exceptions import DBSessionError
from .db_exceptions import DbUrlInvalidError


load_dotenv()
DEV_MODE: bool = os.getenv("DEV_ENV", "False") == "True"


def log_error(err):
    # LOGGER Object
    logger = logging.getLogger(__name__)
    logger.error(err)


def get_db_url(selected_db: str = "DEV_DATABASE_URL") -> str:
    try:
        if len(selected_db) == 0:
            raise ValueError(
                "User did not provide any value for the database url. Please provide a valid database url."
            )

        new_db_url: str | None = os.getenv(selected_db)

        if new_db_url is None:
            raise TypeError(f"Please check environment variables for {selected_db}")
        if len(new_db_url) == 0:
            error = DbUrlInvalidError(
                {
                    "name": "Invalid URL Exception",
                    "description": f"Check env vars. Make sure the value for {selected_db} is on the list of environment variables.",
                }
            )
            raise error
        return new_db_url

    except DbUrlInvalidError as db_url_exc:
        # TODO: log error for operations and development
        log_error(db_url_exc)  # remove this
        raise
    except Exception as exc:
        # TODO: log error for operations and development
        log_error(exc)
        raise


def get_db_engine(db_url: str = "DEV_DATABASE_URL", dev_mode: bool = False):
    return db_engine_factory(db_url=get_db_url(selected_db=db_url), dev_mode=dev_mode)


def get_session(db_engine: Annotated[Engine, Depends(get_db_engine)]):
    try:
        with Session(db_engine) as session:
            yield session
    except SQLAlchemyError as db_exc:
        log_error(db_exc)
        session_err = DBSessionError(
            {
                "name": "db-session-error",
                "description": "A database session operation failed.",
            }
        )
        raise HTTPException(status_code=500, detail=str(session_err)) from db_exc
    except Exception as exc:
        log_error(exc)
        raise HTTPException(
            status_code=500,
            detail="A server-side error occurred while establishing a database session.",
        ) from exc


if __name__ == "__main__":
    DB_ENGINE = Annotated[
        Engine,
        Depends(lambda: db_engine_factory(db_url=get_db_url(), dev_mode=DEV_MODE)),
    ]
