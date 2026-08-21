from __future__ import annotations

import logging
import os
from pathlib import Path

import uvicorn
from app.alnumgen import alnum_generator
from app.db.db import db_engine_factory
from app.db.models.models import ShortiLink
from app.schemas.schemas import GetUrlResponseModel
from app.schemas.schemas import NewUrlSubmissionModel
from dotenv import load_dotenv
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Query
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import OperationalError
from sqlmodel import select
from sqlmodel import Session
from sqlmodel import SQLModel

# LOGGER Object
load_dotenv()
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
DEV_ENV: bool = os.getenv("DEV_ENV", "False") == "True"
db_engine = db_engine_factory(db_url=DATABASE_URL, dev_mode=DEV_ENV)
if db_engine:
    SQLModel.metadata.create_all(db_engine)
# FASTAPI APP Config
app = FastAPI(title="Shorties App")
api_router = APIRouter()
api_version = f"/{os.getenv('API_VERSION')}"
if api_version not in set(["v1", "v2", "v3", "v4", "v5"]):
    api_version = "/v1"


# Routes + Route Handling
@api_router.get(f"{api_version}/healthz/")
def healthz() -> dict:
    with Session(db_engine) as session:
        select_statement = select(ShortiLink)
        result = session.exec(select_statement).first()
        if result:
            return {"status": "alive", "db-connection": "alive"}
    return {"status": "alive", "db-connection": "unknown"}


@api_router.get(f"{api_version}/links/", response_model=list[GetUrlResponseModel])
def get_all_links(
    offeset: int = 0, limit: int = Query(default=20, le=20)
) -> list[GetUrlResponseModel]:
    results: list[GetUrlResponseModel] = []
    try:
        if not db_engine:
            error_dict = {"name": "db-error", "description": "Error with DB Engine!"}
            raise ValueError(error_dict)
        with Session(db_engine) as session:
            select_statement = select(ShortiLink)
            results = [
                GetUrlResponseModel(
                    shorti_key=shorti.shorti_key,
                    shorti_url=shorti.shorti_url,
                    shorti_brand=shorti.brand,
                )
                for shorti in session.exec(statement=select_statement).all()
            ]
            if not results:
                error_dict = {
                    "name": "empty-database-error",
                    "description": "The database is currently empty!",
                }
                raise ValueError(error_dict)
    except ValueError as val_err:
        error_dict = val_err.args[0]
        if error_dict["name"] == "db-error":
            logger.exception(f"error: {error_dict['name']}: {val_err}")
            raise HTTPException(status_code=500, detail=error_dict)
        elif error_dict["name"] == "empty-database-error":
            logger.exception(f"error: {error_dict['name']}: {val_err}")
        else:
            raise
    except Exception as app_exception:
        # all-in-one crapshoot for now.
        logger.exception(
            f"unknown-error: An unknown error occurred in display_all function.\nerror-detail: {app_exception}"
        )
        raise HTTPException(
            status_code=500,
            detail="A server-side error! It's has been logged for review. It will be reviewed ASAP by one our engineers.",
        )
    return results


@api_router.get(f"{api_version}/redirect/" + "{shorti_key}")
def get_url(shorti_key: str) -> RedirectResponse:
    try:
        with Session(db_engine) as current_session:
            select_statement = select(ShortiLink).where(
                ShortiLink.shorti_key == shorti_key
            )
            shorti = current_session.exec(statement=select_statement).first()
            if shorti:
                return RedirectResponse(shorti.shorti_url)
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"This key '{shorti_key}' does not match our records. Verify the key and try again.",
                )

    except HTTPException as err:
        # todo: log error, send failure message, suggestions for retrying.
        response = {
            "key": shorti_key,
            "url": None,
            "status": "failure",
            "message": "We could not redirect this shorti key because the stored URL data was invalid.",
            "error": str(err),
            "suggestions": [
                "Verify the shorti key and try again.",
                "Create a new shorti link if the destination URL is missing or invalid.",
            ],
        }
        logger.exception(
            "HTTPException: Invalid redirect data for shorti key %s: %s",
            shorti_key,
            err,
        )
        raise HTTPException(status_code=err.status_code, detail=response)


@api_router.post(f"{api_version}/create/")
def create_url(url_item: NewUrlSubmissionModel) -> list[GetUrlResponseModel]:
    try:
        if url_item is None or not len(url_item.shorti_url):
            raise HTTPException(
                status_code=404,
                detail="Invalid submission, either url or both url and brand are missing!",
            )

        if url_item and len(url_item.shorti_url) <= 3:
            raise HTTPException(
                status_code=404,
                detail="Invalid submission, missing url. We cannot create a new shorti without a valid url input.",
            )

        new_shorties: list[GetUrlResponseModel] = []
        with Session(db_engine) as session:
            key = alnum_generator()
            validated_shorti = ShortiLink.model_validate(
                {
                    "shorti_key": key,
                    "shorti_url": url_item.shorti_url,
                    "brand": url_item.shorti_brand,
                }
            )
            session.add(validated_shorti)
            session.commit()
            session.refresh(validated_shorti)
            response_item: GetUrlResponseModel = GetUrlResponseModel.model_validate(
                {
                    **validated_shorti.model_dump(),
                    "shorti_brand": validated_shorti.brand,
                }
            )
            new_shorties.append(response_item)
            return new_shorties
        raise Exception(
            status_code=404,
            detail="Unknown Error Occurred. We have recorded this and notified the operators of this service.",
        )
    except IntegrityError as integrity_err:
        logger.exception(
            f"IntegrityError: An error occurred while inserting a new shorti link: {integrity_err}"
        )
        raise HTTPException(
            status_code=400,
            detail="A database integrity error occurred while creating a new shorti link. Please ensure the data is valid and try again.",
        )
    except OperationalError as op_err:
        logger.exception(
            f"OperationalError: An error occurred while checking for existing shorti key: {op_err}"
        )
        raise HTTPException(
            status_code=500,
            detail="A server-side error occurred while checking for existing shorti key. Please try again later.",
        )
    except HTTPException as err:
        # todo: log error, send failure message, suggestions for retrying.
        # response = {
        #     "url": None,
        #     "status": "failure",
        #     "message": "We could not create a new link.",
        #     "error": str(err),
        #     "suggestions": ["Verify your submitted data and try again."],
        # }
        logger.exception(f"Error: HTTPException: {err}")
        raise
    except Exception as err:
        new_exception = f"Error: Exception: {err}"
        logger.exception(new_exception)
        raise HTTPException(status_code=500, detail=new_exception)


@api_router.delete(f"{api_version}/delete/" + "{shorti_key}")
def delete_a_shorti(shorti_key: str):
    print("shorti_key:", shorti_key)
    deleted_items = []
    try:
        if shorti_key is None or shorti_key == "" or len(shorti_key) < 4:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "failure",
                    "message": f"We could not DELETE this key: {shorti_key}!",
                },
            )
        with Session(db_engine) as session:
            if shorti_key:
                select_statement = select(ShortiLink).where(
                    ShortiLink.shorti_key == shorti_key
                )
                lookup_results = session.exec(statement=select_statement).all()
                for result in lookup_results:
                    new_response_item = GetUrlResponseModel(
                        shorti_key=result.shorti_key,
                        shorti_url=result.shorti_url,
                        shorti_brand=result.brand,
                    )
                    deleted_items.append(new_response_item)
                    session.delete(result)
                session.commit()
            else:
                raise HTTPException(
                    status_code=404,
                    detail="status='failure' "
                    + f"message='We did not find any result for keyword: {shorti_key}'",
                )

        if deleted_items:
            return deleted_items
        else:
            raise HTTPException(
                status_code=404,
                detail={
                    "deletion-status": "failed",
                    "message": "We did not find any result for keyword: {shorti_key}",
                    "status_code": 404,
                },
            )

    except HTTPException as httpErr:
        logger.info("HTTPException while creating shorti: %s", httpErr)
        raise


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
