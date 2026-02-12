from __future__ import annotations

import os

from sqlmodel import create_engine
from sqlmodel import SQLModel


def db_engine_factory(db_url: str, dev_mode=False):
    try:
        if db_url is None:
            raise ValueError("A URL path is required.")
        return create_engine(db_url, echo=dev_mode)
    except ValueError as valErr:
        print("url-path-error:", valErr)
        return None


if __name__ == "__main__":
    DATABASE_URL = os.getenv("DATABASE_URL")
    DEV_ENV = os.getenv("DEV_ENV")
    if DATABASE_URL:
        db_engine = db_engine_factory(db_url=DATABASE_URL, dev_mode=DEV_ENV)
        if db_engine:
            SQLModel.metadata.create_all(
                db_engine
            )  # will create a DB without any table
