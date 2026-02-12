from __future__ import annotations

import os

from sqlmodel import create_engine
from sqlmodel import Session


def app_db_engine(db_url: str = "sqlite:///memory", debug_mode: bool = False):
    try:
        if not isinstance(db_url, str):
            raise ValueError("")
        if db_url:
            return create_engine(url=db_url, echo=debug_mode)
        else:
            raise ValueError("Could not create a ")
    except ValueError as valErr:
        print(f"error: {valErr}")  # TODO: Log


if __name__ == "__main__":
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL:
        db_ngin = app_db_engine(db_url=DATABASE_URL)
    if db_ngin:
        session = Session(db_ngin)
