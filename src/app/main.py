from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import AnyUrl
from typing import Optional
from models.main import URLRequestModel, UrlResponseModel
from app.alnumgen import alnum_generator
# from app.constants import KEY_MAX


app = FastAPI(title="Shorties App")
api_router = APIRouter()
api_version = "/v1"
shorti_links = {
    "scap": "https://www.scapital.com",
    "goog": "https://www.google.com",
    "meta": "https://www.facebook.com",
    "twit": "https://www.twitter.com",
    "link": "https://www.linkedin.com",
    "gith": "https://www.github.com",
    "redd": "https://www.reddit.com",
    "yout": "https://www.youtube.com",
    "inst": "https://www.instagram.com",
    "micr": "https://www.microsoft.com",
    "appl": "https://www.apple.com",
}
click_event = {}


@api_router.get(f"{api_version}/healthz/")
def healthz() -> dict:
    return {"status": "alive"}


@api_router.get(f"{api_version}/display/")
def display_all(max_results: Optional[int] = None) -> dict:
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
            raise TypeError("The key provided is not of a valid type. Key must be a str.")
        if key in store:
            return {
                "key": f"{key}",
                "url": store.get(key),
                "status": "success",
                "message": f'success: url matching "{key}"  was found!',
            }
        else:
            raise HTTPException(
                status_code=404, detail="failure: this key does not match our records. Verify the key and try again."
            )

    except HTTPException as err:
        print(err)  # todo: log error, send failure message, suggestions for retrying.
        raise err
    except ValueError as err:
        print(f"invalid-data-error: {err}")  # todo: log error, send failure message, suggestions for retrying.
        return {
            "key": f"{key}",
            "url": None,
            "status": "failure",
            "message": f"value-not-found-error: {err}",
        }
    except TypeError as err:
        print(f"invalid-data-error: {err}")  # todo: log error, send failure message, suggestions for retrying.
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

        store[key] = url_item
        new_url_item = UrlResponseModel(
            key=key,
            brand=store[key].brand,
            url=AnyUrl(store[key].url),
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
    uvicorn.run("main:app", reload=True, host=HOST, port=PORT, log_level="debug")
