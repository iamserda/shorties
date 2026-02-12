from __future__ import annotations

import os

from sqlmodel import create_engine
from sqlmodel import SQLModel


def db_engine_factory(db_url: str, dev_mode=False):
    try:
        if db_url is None:
            raise ValueError("A URL path is required.")
        db_engine = create_engine(db_url, echo=dev_mode)
        if db_engine is None:
            raise ValueError(
                "Failed to create DB ENGINE. Check the URL argument. Check sys/admin/dev logs for more details!"
            )
        return db_engine
    except ValueError as valErr:
        print("url-path-error:", valErr)  # TODO: Logger!
        return None


if __name__ == "__main__":
    DATABASE_URL = os.getenv("DATABASE_URL")
    DEV_ENV: bool = os.getenv("DEV_ENV", "False") == "True"
    if DATABASE_URL:
        db_engine = db_engine_factory(db_url=DATABASE_URL, dev_mode=DEV_ENV)
        if db_engine:
            SQLModel.metadata.create_all(
                db_engine
            )  # will create a DB without any table
