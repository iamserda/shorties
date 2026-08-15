from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import create_engine
from sqlmodel import SQLModel


def log_error(err):
    # LOGGER Object
    logger = logging.getLogger(__name__)
    logger.error(err, exc_info=True)


def db_engine_factory(db_url: str | None, dev_mode: bool = False, **engine_kwargs):
    try:
        if not isinstance(db_url, str):
            type_err = TypeError("Invalid type for Database URL. Expecting a string...")
            raise type_err
        if db_url == "":
            val_err = ValueError(
                "DB URL provided is not valid. DB URL cannot be empty."
            )
            raise val_err
        return create_engine(db_url, echo=dev_mode, **engine_kwargs)

    except (TypeError, ValueError) as err:
        log_error(err)
        raise

    except SQLAlchemyError as err:
        log_error(err)
        raise


def dev_create_db() -> None:
    # For DEV-ENV only.
    # This runs in script mode and NOT as part of the application.
    # This is being used to create the DB for the first time if it does not already exist.
    # This is strictly for SQLite dev environment.
    # TODO: Move DB to postgres SQL. This section will NO LONGER BE NEEDED.
    # Come to think of it, maybe I should make this its own file within db or elsewhere considering its purpose.
    # It does not belong here.

    load_dotenv()
    APP_DIR = Path(__file__).resolve().parent.parent
    LOGS_DIR = APP_DIR.joinpath("logs")
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    LOGFILE_PATH = LOGS_DIR.joinpath("db.log")
    logging.basicConfig(
        filename=LOGFILE_PATH,
        level=logging.DEBUG,
        datefmt="%m/%d/%Y %I:%M:%S %p",
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    DATABASE_URL = os.getenv("DEV_DATABASE_URL")
    DEV_ENV: bool = os.getenv("DEV_ENV", "False") == "True"
    db_engine = db_engine_factory(db_url=DATABASE_URL, dev_mode=DEV_ENV)
    try:
        SQLModel.metadata.create_all(db_engine)  # will create a DB without any table
    except SQLAlchemyError as err:
        log_error(err)
        raise


if __name__ == "__main__":
    dev_create_db()
