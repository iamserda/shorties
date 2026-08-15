from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from app.api.routes import healthz
from app.api.routes import links
from app.core.config import get_settings
from app.db.db_exceptions import DBEngineError
from app.db.engine import create_db_engine
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel

# Logger Configuration
APP_DIR = Path(__file__).resolve().parent
LOGS_DIR = APP_DIR.joinpath("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)
APPLOG_PATH = LOGS_DIR.joinpath("main.log")
logging.basicConfig(
    filename=APPLOG_PATH,
    level=logging.INFO,
    datefmt="%m/%d/%Y %I:%M:%S %p",
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

# Database Engine Initialization
# create_db_engine() is cached (see app/db/engine.py), so this returns the
# same Engine instance every time it's called anywhere in the app. Routes
# resolve their session through this module-level attribute (rather than
# calling create_db_engine() directly), so it can be swapped out in tests.
db_engine: Engine = create_db_engine()


def populate_db(db_engine: Engine) -> None:
    SQLModel.metadata.create_all(bind=db_engine)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Runs in whichever process actually serves requests, including
    # uvicorn's reload worker subprocess (unlike code gated behind
    # `if __name__ == "__main__":`, which only runs in the launcher).
    populate_db(db_engine)
    yield


# FASTAPI APP Config
app = FastAPI(title="Shorties App", lifespan=lifespan)


@app.exception_handler(DBEngineError)
async def db_engine_error_handler(request: Request, exc: DBEngineError) -> JSONResponse:
    # Catches DBEngineError (and its subclass DBSessionError) raised during
    # dependency resolution, e.g. get_db_session — those happen before a
    # route body's own try/except ever runs, so they need a handler here.
    return JSONResponse(
        status_code=500,
        content={
            "detail": {
                "error": {
                    "type": exc.__class__.__name__,
                    "description": exc.description,
                    "status-code": 500,
                    "message": "A server-side error occurred! It's has been logged for technical review. It will be reviewed ASAP by one our engineers.",
                }
            }
        },
    )


# API Version Configuration
API_VERSION = get_settings().api_version

# Routes + Route Handling
app.include_router(healthz.router, prefix=f"/{API_VERSION}")
app.include_router(links.router, prefix=f"/{API_VERSION}", tags=["Links"])

# Run the application, if this script is executed directly (not imported as a module).
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        reload=True,
        host="0.0.0.0",
        port=8001,
        log_level="debug",
    )
