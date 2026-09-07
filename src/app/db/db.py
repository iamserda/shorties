from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import create_engine
from sqlmodel import SQLModel

from .db_exceptions import DBEngineError
from .db_exceptions import DbUrlInvalidError


def log_error(err: Exception, err_type: str = "error"):
    """Log an exception at the requested logging level."""
    logger = logging.getLogger(__name__)
    log_methods = {
        "debug": logger.debug,
        "info": logger.info,
        "warning": logger.warning,
        "error": logger.error,
        "exception": logger.exception,
        "critical": logger.critical,
    }
    level = err_type.lower()
    log_method = log_methods.get(level, logger.error)
    if level == "exception":
        log_method(err, exc_info=True)
    else:
        log_method(err)


def db_engine_factory(db_url: str | None, dev_mode: bool = False):
    try:
        if not isinstance(db_url, str):
            type_err = TypeError("Invalid type for Database URL. Expecting a string...")
            raise type_err
        if db_url == "":
            val_err = DbUrlInvalidError(
                {
                    "name": "invalid-url-error",
                    "description": "A URL was not provided. A valid URL is required.",
                },
                message="",
            )
            raise val_err
        return create_engine(url=db_url, echo=dev_mode)

    except TypeError as type_err:
        log_error(type_err)
        raise HTTPException(status_code=400, detail=str(type_err)) from type_err

    except DbUrlInvalidError as db_url_err:
        log_error(db_url_err)
        raise HTTPException(status_code=400, detail=str(db_url_err)) from db_url_err
    except (DBEngineError, SQLAlchemyError) as sql_err:
        log_error(sql_err, err_type="exception")
        raise HTTPException(status_code=400, detail=str(sql_err)) from sql_err
    except Exception as gen_exc:
        log_error(gen_exc, err_type="exception")
        raise HTTPException(
            status_code=400,
            detail=str("Bad Request. Please check your submitted data and try again!"),
        ) from gen_exc


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
    create_dev_db()
