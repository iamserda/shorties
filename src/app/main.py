from __future__ import annotations

import os

from app.db.db import db_engine_factory
from app.db.models.models import ShortiLink
from fastapi import APIRouter
from fastapi import FastAPI
from sqlmodel import select
from sqlmodel import Session
from sqlmodel import SQLModel

DATABASE_URL = "sqlite:///src/app/db/SHORTIES_DATABASE.db"
DEV_ENV: bool = os.getenv("DEV_ENV", "False") == "True"
db_engine = db_engine_factory(db_url=DATABASE_URL, dev_mode=DEV_ENV)

if db_engine:
    SQLModel.metadata.create_all(db_engine)

app = FastAPI(title="Shorties App")
api_router = APIRouter()
api_version = os.getenv("API_VERSION")


if not api_version:
    api_version = "/v1"


@api_router.get(f"{api_version}/healthz/")
def healthz() -> dict:
    return {"status": "alive"}


@api_router.get(f"{api_version}/display/")
def display_all() -> list:
    try:
        if not db_engine:
            raise ValueError("Error with DB Engine!")
        with Session(db_engine) as session:
            select_statement = select(ShortiLink)
            results = session.exec(statement=select_statement).all()
            for r in results:
                print(r)
            return list(results)
    except Exception as err:
        print("Error:", err)
        return []


# @api_router.get(f"{api_version}/redirect/")
# def get_url(key: str) -> dict:
#     store = shorti_links
#     try:
#         if not key:
#             raise ValueError("Invalid, user did not provide a key.")
#         if not isinstance(key, str):
#             raise TypeError(
#                 "The key provided is not of a valid type. Key must be a str.",
#             )
#         if key in store:
#             return {
#                 "key": f"{key}",
#                 "url": store.get(key),
#                 "status": "success",
#                 "message": f'success: url matching "{key}"  was found!',
#             }
#         else:
#             raise HTTPException(
#                 status_code=404,
#                 detail="failure: this key does not match our records. Verify the key and try again.",
#             )

#     except HTTPException as err:
#         # todo: log error, send failure message, suggestions for retrying.
#         print(err)
#         raise err
#     except ValueError as err:
#         # todo: log error, send failure message, suggestions for retrying.
#         print(f"invalid-data-error: {err}")
#         return {
#             "key": f"{key}",
#             "url": None,
#             "status": "failure",
#             "message": f"value-not-found-error: {err}",
#         }
#     except TypeError as err:
#         # todo: log error, send failure message, suggestions for retrying.
#         print(f"invalid-data-error: {err}")
#         return {
#             "key": f"{key}",
#             "url": None,
#             "status": "failure",
#             "message": f"type-validity-error: {err}",
#         }


# @api_router.post(f"{api_version}/create/")
# def create_url(url_item: URLRequestModel) -> UrlResponseModel:
#     store = shorti_links
#     key: str = alnum_generator()
#     print(url_item)
#     try:
#         while key in store:
#             key = alnum_generator()

#         new_brand: str = url_item.brand
#         new_url: str = url_item.url
#         store[key]: dict = {"brand": new_brand, "url": new_url}
#         new_url_item = UrlResponseModel(
#             key=key,
#             brand=store[key]["brand"],
#             url=AnyUrl(store[key]["url"]),
#             status="success",
#             message="A key was successfully generated",
#         )
#         if key in store:
#             return new_url_item

#         # failed = UrlResponseModel(
#         #     key=key,
#         #     brand="",
#         #     url="",
#         #     status="failure",
#         #     message="We could not create a new key at this moment. Please try again later!",
#         # )
#         # return failed
#         raise HTTPException(
#             status_code=404,
#             detail="status='failure', message='We could not create a new key at this moment!'",
#         )
#     except HTTPException as err:
#         print(err)  # todo: logg
#         raise err


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
