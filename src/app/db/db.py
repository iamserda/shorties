from __future__ import annotations

import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import create_engine


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
