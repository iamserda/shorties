from __future__ import annotations

import os
from typing import Annotated

from app.db.db import db_engine_factory
from dotenv import load_dotenv
from fastapi import Depends
from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session


load_dotenv()
DEV_MODE: bool = os.getenv("DEV_ENV", "False") == "True"


class DbUrlInvalidError(ValueError):
    message: str = "Invalid DB URL was provided. Please check the URL and try again."


class SessionError(SQLAlchemyError):
    pass


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
            error = DbUrlInvalidError()
            error.message = f"Check env vars. Make sure the value for {selected_db} is on the list of environment variables."
            raise error
        return new_db_url

    except SQLAlchemyError as db_exc:
        # TODO: log error for operations and development
        print(db_exc)  # remove this
        raise
    except Exception:
        # TODO: log error for operations and development
        raise


def get_db_engine(db_url: str = "DEV_DATABASE_URL", dev_mode: bool = False):
    return db_engine_factory(db_url=get_db_url(selected_db=db_url), dev_mode=dev_mode)


def get_session(db_engine: Annotated[Engine, Depends(get_db_engine)]):
    try:
        with Session(db_engine) as session:
            yield session
    except SessionError as session_exc:
        # TODO: log error for operations and development
        print(session_exc)  # remove this
        raise
    except SQLAlchemyError as db_exc:
        # TODO: log error for operations and development
        print(db_exc)  # remove this
        raise
    except Exception as _exc:
        # TODO: log error for operations and development
        print(_exc)  # remove this
        raise


if __name__ == "__main__":
    DB_ENGINE = Annotated[
        Engine,
        Depends(lambda: db_engine_factory(db_url=get_db_url(), dev_mode=DEV_MODE)),
    ]
