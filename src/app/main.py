from __future__ import annotations

import logging
import os
from collections.abc import Sequence

from app.alnumgen import alnum_generator
from app.db.db import db_engine_factory
from app.db.models.models import ShortiLink
from app.schemas.schemas import GetURLRequestModel
from app.schemas.schemas import GetUrlResponseModel
from app.schemas.schemas import NewUrlSubmissionModel
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import HTTPException
from sqlmodel import select
from sqlmodel import Session
from sqlmodel import SQLModel

# LOGGER Object
logger = logging.getLogger(__name__)
logging.basicConfig(filename="src/app/logs/main.log", level=logging.INFO)

# Database Config:
DATABASE_URL = "sqlite:///src/app/db/SHORTIES_DATABASE.db"
DEV_ENV: bool = os.getenv("DEV_ENV", "False") == "True"
db_engine = db_engine_factory(db_url=DATABASE_URL, dev_mode=DEV_ENV)
if db_engine:
    SQLModel.metadata.create_all(db_engine)

# FASTAPI APP Config
app = FastAPI(title="Shorties App")
api_router = APIRouter()
api_version = os.getenv("API_VERSION")
if not api_version:
    api_version = "/v1"


# Routes + Route Handling
@api_router.get(f"{api_version}/healthz/")
def healthz() -> dict:
    return {"status": "alive"}


@api_router.get(f"{api_version}/display/")
def display_all() -> Sequence:
    try:
        if not db_engine:
            raise ValueError("Error with DB Engine!")
        with Session(db_engine) as session:
            select_statement = select(ShortiLink)
            return session.exec(statement=select_statement).all()
    except Exception as err:
        print("Error:", err)
        return []


@api_router.get(f"{api_version}/redirect/", status_code=301)
def get_url(shorti_key: str | dict | GetURLRequestModel) -> GetUrlResponseModel | dict:
    try:
        print(shorti_key)
        if not shorti_key:
            raise ValueError("Invalid, user did not provide a key.")

        if (
            not isinstance(shorti_key, str)
            and not isinstance(shorti_key, GetURLRequestModel)
            and not isinstance(shorti_key, dict)
        ):
            raise TypeError("The key provided is not of a valid type.")

        with Session(db_engine) as current_session:
            if isinstance(shorti_key, GetURLRequestModel):
                shorti_key = shorti_key.key
            elif isinstance(shorti_key, dict):
                shorti_key = shorti_key["shorti_key"]

            select_statement = select(ShortiLink).where(
                ShortiLink.shorti_key == shorti_key
            )
            result = current_session.exec(statement=select_statement).all()
            if result:
                new_shorti = result[0]
                return GetUrlResponseModel(
                    key=new_shorti.shorti_key,
                    brand=new_shorti.brand,
                    url=new_shorti.shorti_url,
                    message=f'success: url matching "{shorti_key}"  was found!',
                    status="Success!",
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"message: Request-Failed: 'This key {shorti_key} does not match our records. Verify the key and try again.",
                )

    except HTTPException as err:
        # todo: log error, send failure message, suggestions for retrying.
        print(err)
        raise err
    except ValueError as err:
        # todo: log error, send failure message, suggestions for retrying.
        print(f"invalid-data-error: {err}")
        return {
            "key": f"{shorti_key}",
            "url": None,
            "status": "failure",
            "message": f"value-not-found-error: {err}",
        }
    except TypeError as err:
        # todo: log error, send failure message, suggestions for retrying.
        print(f"invalid-data-error: {err}")
        return {
            "key": f"{shorti_key}",
            "url": None,
            "status": "failure",
            "message": f"type-validity-error: {err}",
        }


@api_router.post(f"{api_version}/create/")
def create_url(url_item: NewUrlSubmissionModel) -> Sequence[GetUrlResponseModel]:
    if url_item is None or not len(url_item.url):
        raise HTTPException(
            status_code=404,
            detail="Invalid submission, either url or both url and brand are missing!",
        )

    if url_item and len(url_item.url) <= 3:
        raise HTTPException(
            status_code=404,
            detail="Invalid submission, missing url. We cannot create a new shorti without a valid url input.",
        )

    key: str = alnum_generator()
    new_shorties: list[GetUrlResponseModel] = []
    try:
        with Session(db_engine) as session:
            select_statement = select(ShortiLink).where(ShortiLink.shorti_key == key)
            result = session.exec(statement=select_statement).all()
            while result:
                key = alnum_generator()
                select_statement = select(ShortiLink).where(
                    ShortiLink.shorti_key == key
                )
                result = session.exec(statement=select_statement).all()

            new_shorti = ShortiLink(
                shorti_key=key, shorti_url=str(url_item.url), brand=url_item.brand
            )
            session.add(new_shorti)
            session.commit()

            select_statement = select(ShortiLink).where(ShortiLink.shorti_key == key)
            shorties: Sequence = session.exec(statement=select_statement).all()
            if shorties:
                new_shorties = [
                    GetUrlResponseModel(
                        key=shorti.shorti_key,
                        brand=shorti.brand,
                        url=shorti.shorti_url,
                        status="success",
                        message="A key was successfully generated. We stored your url! You can start using your new short url immediately.",
                    )
                    for shorti in shorties
                ]
            else:
                raise HTTPException(
                    status_code=404,
                    detail="status='failure', message='We could not create a new key at this moment!'",
                )
        return new_shorties
    except HTTPException as httpErr:
        logger.exception("HTTPException while creating shorti: %s", httpErr)
        return new_shorties


@api_router.delete(f"{api_version}/delete/")
def delete_a_shorti(shorti_key: str):
    results = []
    try:
        if shorti_key is None or shorti_key == "" or len(shorti_key) < 4:
            raise HTTPException(
                status_code=404,
                detail="status='failure', message='We could not create a new key at this moment!'",
            )
        with Session(db_engine) as session:
            if shorti_key:
                select_statement = select(ShortiLink).where(
                    ShortiLink.shorti_key == shorti_key
                )
                result = session.exec(statement=select_statement).all()
                if result:
                    shorti = result[0]
                    new_response_item = GetUrlResponseModel(
                        key=shorti.shorti_key, url=shorti.shorti_url
                    )
                    session.delete(shorti)
                    session.commit()
                    new_response_item.message = "Deleted Successfully!"
                    new_response_item.status = "deleted"
                    results.append(new_response_item)
                else:
                    raise HTTPException(
                        status_code=404,
                        detail="status='failure' "
                        + f"message='We did not find any result for keyword: {shorti_key}'",
                    )
    except HTTPException as httpErr:
        logger.info("HTTPException while creating shorti: %s", httpErr)
        return [httpErr]
    return results


app.include_router(api_router)
if __name__ == "__main__":
    import uvicorn

    HOST: str = "0.0.0.0"
    PORT: int = 8001
    uvicorn.run(
        "main:app",
        reload=True,
        host=HOST,
        port=PORT,
        log_level="debug",
    )
