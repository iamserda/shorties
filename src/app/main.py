from __future__ import annotations

from app.alnumgen import alnum_generator
from app.schemas.schemas import URLRequestModel
from app.schemas.schemas import UrlResponseModel
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import AnyUrl


app = FastAPI(title="Shorties App")
api_router = APIRouter()
api_version = "/v1"
shorti_links: dict = {
    "scap": {"brand": "scap", "url": "https://www.scapital.com"},
    "goog": {"brand": "goog", "url": "https://www.google.com"},
    "meta": {"brand": "meta", "url": "https://www.facebook.com"},
    "twit": {"brand": "twit", "url": "https://www.twitter.com"},
    "link": {"brand": "link", "url": "https://www.linkedin.com"},
    "gith": {"brand": "gith", "url": "https://www.github.com"},
    "redd": {"brand": "redd", "url": "https://www.reddit.com"},
    "yout": {"brand": "yout", "url": "https://www.youtube.com"},
    "inst": {"brand": "inst", "url": "https://www.instagram.com"},
    "micr": {"brand": "micr", "url": "https://www.microsoft.com"},
    "appl": {"brand": "appl", "url": "https://www.apple.com"},
    "amaz": {"brand": "amaz", "url": "https://www.amazon.com"},
    "netf": {"brand": "netf", "url": "https://www.netflix.com"},
    "spof": {"brand": "spof", "url": "https://www.spotify.com"},
    "slac": {"brand": "slac", "url": "https://www.slack.com"},
    "drop": {"brand": "drop", "url": "https://www.dropbox.com"},
    "adob": {"brand": "adob", "url": "https://www.adobe.com"},
    "uber": {"brand": "uber", "url": "https://www.uber.com"},
    "airb": {"brand": "airb", "url": "https://www.airbnb.com"},
    "tesl": {"brand": "tesl", "url": "https://www.tesla.com"},
    "nyti": {"brand": "nyti", "url": "https://www.nytimes.com"},
    "wash": {"brand": "wash", "url": "https://www.washingtonpost.com"},
    "bbc": {"brand": "bbc", "url": "https://www.bbc.com"},
    "cnn": {"brand": "cnn", "url": "https://www.cnn.com"},
    "espn": {"brand": "espn", "url": "https://www.espn.com"},
    "pint": {"brand": "pint", "url": "https://www.pinterest.com"},
    "tumblr": {"brand": "tumblr", "url": "https://www.tumblr.com"},
    "quor": {"brand": "quor", "url": "https://www.quora.com"},
    "yaho": {"brand": "yaho", "url": "https://www.yahoo.com"},
    "ebay": {"brand": "ebay", "url": "https://www.ebay.com"},
    "payp": {"brand": "payp", "url": "https://www.paypal.com"},
    "tikt": {"brand": "tikt", "url": "https://www.tiktok.com"},
}
click_event: dict = {}


@api_router.get(f"{api_version}/healthz/")
def healthz() -> dict:
    return {"status": "alive"}


@api_router.get(f"{api_version}/display/")
def display_all(max_results: int | None = None) -> dict:
    store = shorti_links
    if max_results is None or max_results <= 0 or max_results >= len(store):
        return store
    else:
        results = {}
        for i, (k, v) in enumerate(store.items()):
            if i >= max_results:
                break
            else:
                results[k] = v
        return results


@api_router.get(f"{api_version}/redirect/")
def get_url(key: str) -> dict:
    store = shorti_links
    try:
        if not key:
            raise ValueError("Invalid, user did not provide a key.")
        if not isinstance(key, str):
            raise TypeError(
                "The key provided is not of a valid type. Key must be a str.",
            )
        if key in store:
            return {
                "key": f"{key}",
                "url": store.get(key),
                "status": "success",
                "message": f'success: url matching "{key}"  was found!',
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="failure: this key does not match our records. Verify the key and try again.",
            )

    except HTTPException as err:
        # todo: log error, send failure message, suggestions for retrying.
        print(err)
        raise err
    except ValueError as err:
        # todo: log error, send failure message, suggestions for retrying.
        print(f"invalid-data-error: {err}")
        return {
            "key": f"{key}",
            "url": None,
            "status": "failure",
            "message": f"value-not-found-error: {err}",
        }
    except TypeError as err:
        # todo: log error, send failure message, suggestions for retrying.
        print(f"invalid-data-error: {err}")
        return {
            "key": f"{key}",
            "url": None,
            "status": "failure",
            "message": f"type-validity-error: {err}",
        }


@api_router.post(f"{api_version}/create/")
def create_url(url_item: URLRequestModel) -> UrlResponseModel:
    store = shorti_links
    key = alnum_generator()
    print(url_item)
    try:
        while key in store:
            key = alnum_generator()

        new_brand = url_item.brand
        new_url = url_item.url
        store[key] = {"brand": new_brand, "url": new_url}
        new_url_item = UrlResponseModel(
            key=key,
            brand=store[key]["brand"],
            url=AnyUrl(store[key]["url"]),
            status="success",
            message="A key was successfully generated",
        )
        if key in store:
            return new_url_item

        # failed = UrlResponseModel(
        #     key=key,
        #     brand="",
        #     url="",
        #     status="failure",
        #     message="We could not create a new key at this moment. Please try again later!",
        # )
        # return failed
        raise HTTPException(
            status_code=404,
            detail="status='failure', message='We could not create a new key at this moment!'",
        )
    except HTTPException as err:
        print(err)  # todo: logg
        raise err


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
