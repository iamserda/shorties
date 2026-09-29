from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import AnyUrl
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import create_engine
from sqlmodel import SQLModel


def db_engine_factory(db_url: AnyUrl | str, dev_mode: bool = False):
    if not isinstance(db_url, str):
        raise TypeError("Invalid type for Database URL. Expecting a string...")

    if db_url == "":
        raise ValueError(
            "The Database URL was not provided. A valid Database URL is required."
        )
    try:
        new_db_engine = create_engine(url=db_url, echo=dev_mode)
        return new_db_engine
    except SQLAlchemyError as err:
        logging.exception(
            "sql_alchemy_error -> function db_engine_factory: %s", err, exc_info=True
        )
        raise
    except Exception as gen_exc:
        logging.exception(
            "general_error -> function db_engine_factory: %s", gen_exc, exc_info=True
        )
        raise


def create_dev_db() -> None:
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
    DATABASE_URL = os.getenv("DEV_DATABASE_URL")
    DATABASE_URL = DATABASE_URL if DATABASE_URL else ""
    DEV_ENV: bool = os.getenv("DEV_ENV", "False") == "True"

    logging.basicConfig(
        filename=LOGFILE_PATH,
        level=logging.DEBUG,
        datefmt="%m/%d/%Y %I:%M:%S %p",
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logger = logging.getLogger(__name__)

    try:
        db_engine = db_engine_factory(db_url=DATABASE_URL, dev_mode=DEV_ENV)
        SQLModel.metadata.create_all(db_engine)  # will create a DB without any table
    except SQLAlchemyError as err:
        logger.exception(
            "sql_alchemy_error -> function create_dev_db: %s", err, exc_info=True
        )
        raise
    except Exception as gen_exc:
        logger.exception(
            "general_error -> function create_dev_db: %s", gen_exc, exc_info=True
        )
        raise


if __name__ == "__main__":
    create_dev_db()
