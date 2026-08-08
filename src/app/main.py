from __future__ import annotations

import logging
import os
from pathlib import Path

import uvicorn
from app.db.db import db_engine_factory
from app.db.db_exceptions import DBEngineError
from app.db.db_exceptions import EmptyDatabaseError
from app.db.models.models import ShortiLink
from app.schemas.schemas import GetUrlResponseModel
from app.schemas.schemas import GetUrlsResponseModel
from dotenv import load_dotenv
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Query
from sqlmodel import select
from sqlmodel import Session
from sqlmodel import SQLModel


# LOGGER Object
load_dotenv()
API_VERSIONS = (
    eval(os.getenv("API_VERSIONS", "[/v1]")) if os.getenv("API_VERSIONS") else ["/v1"]
)
API_VERSION = (
    API_VERSIONS[0] if isinstance(API_VERSIONS, list) and API_VERSIONS else "/v1"
)
DEV_ENV: bool = os.getenv("DEV_ENV", "False") == "True"
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
logger = logging.getLogger(__name__)

# Database Config:
DATABASE_URL: str = (
    str(os.getenv("DEV_DATABASE_URL"))
    if os.getenv("DEV_DATABASE_URL")
    else "sqlite:///:memory:"
)

db_engine = db_engine_factory(db_url=DATABASE_URL, dev_mode=DEV_ENV)
db_engine = None
if db_engine:
    SQLModel.metadata.create_all(db_engine)
# FASTAPI APP Config
app = FastAPI(title="Shorties App")
api_router = APIRouter()

if not API_VERSION:
    API_VERSION = "/v1"


# Routes + Route Handling
@api_router.get(f"/{API_VERSION}/healthz/")
async def healthz() -> dict:
    return {"status": "alive"}


@api_router.get(f"/{API_VERSION}/links/", response_model=GetUrlsResponseModel)
async def get_all_links(
    offset: int = Query(default=0, ge=0), limit: int = Query(default=20, le=20)
) -> GetUrlsResponseModel:

    results = GetUrlsResponseModel(urls=[])
    db_engine_error = {
        "name": "db-error",
        "description": "An error occurred with DB Engine!",
    }
    empty_db_error = {
        "name": "empty-database-error",
        "description": "Our database is currently empty! Please create a new link via the API enpoints for creating new links and try again. See our documentation for more information.",
    }
    common_error_message = "A server-side error occurred! It's has been logged for technical review. It will be reviewed ASAP by one our engineers."
    try:
        if not db_engine:
            raise DBEngineError(db_engine_error)
        with Session(db_engine) as session:
            if not session:
                raise DBEngineError(db_engine_error)
            select_statement = select(ShortiLink).offset(offset).limit(limit)
            new_urls = [
                GetUrlResponseModel(
                    key=shorti.shorti_key, url=shorti.shorti_url, brand=shorti.brand
                )
                for shorti in session.exec(statement=select_statement).all()
            ]
            results.urls = new_urls
            if not results.urls:
                raise EmptyDatabaseError(empty_db_error)
    except EmptyDatabaseError as empty_db_err:
        logger.info(
            f"error: {empty_db_err.description}",
            exc_info=True,
        )
        return GetUrlsResponseModel(urls=[])
    except DBEngineError as db_engine_err:
        STATUS_CODE = 500
        logger.exception(
            f"error: {db_engine_err}",
            exc_info=True,
        )
        new_db_engine_error = {
            "error": {
                "type": db_engine_err.__class__.__name__,
                "description": db_engine_err.description,
                "status-code": STATUS_CODE,
                "message": common_error_message,
            }
        }
        raise HTTPException(status_code=500, detail=new_db_engine_error)
    except HTTPException as httpErr:
        logger.info(
            f"A generic HTTP Exception occurred while getting links from database: {httpErr}"
        )
        raise
    except Exception as app_exception:
        # all-in-one crapshoot for now.
        logging_message = f"An unexpected error occurred while getting links from database: {app_exception}"
        logger.exception(
            logging_message,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=common_error_message,
        )
    return results


app.include_router(api_router)
if __name__ == "__main__":
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    if db_engine:
        uvicorn.run(
            "main:app",
            reload=True,
            host=HOST,
            port=PORT,
            log_level="debug",
        )
