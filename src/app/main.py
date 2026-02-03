from fastapi import FastAPI, APIRouter

from models.main import URLModel, UrlResponseModel
from app.alnumgen import alnum_generator
# from app.constants import KEY_MAX


app = FastAPI(title="Shorties App")
api_router = APIRouter()
store = {
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


@api_router.get("/healthz")
def healthz() -> dict:
    return {"status": "alive"}

@api_router.get("/displayall")
def display_all() -> dict:
    return store

@api_router.get("/redirect/{key}")
def get_url(key: str) -> dict:
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
        raise KeyError("failure: this key does not match our records. Verify the key and try again.")
    except KeyError as err:
        print(err)  # todo: log error, send failure message, suggestions for retrying.
        return {
            "key": f"{key}",
            "url": None,
            "status": "failure",
            "message": f"key-not-found-error: {err}",
        }
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


@api_router.post("/create")
def create_url(url_item: URLModel) -> UrlResponseModel:
    key = alnum_generator()
    try:
        while key in store:
            key = alnum_generator()
        store[key] = url_item
        if key in store:
            return UrlResponseModel(
                key=key,
                brand=store[key].brand,
                url=store[key].url,
                status="success",
                message="A key was successfully generated",
            )
        else:
            return UrlResponseModel(
                key=key,
                brand="",
                url="",
                status="failure",
                message="We could not create a new key at this moment. Please try again later!",
            )
    except KeyError as err:
        print(err)  # todo: logg
        pass

app.include_router(api_router)
if __name__ == "__main__":
    import uvicorn
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    uvicorn.run("main:app", reload=True, host=HOST, port=PORT, log_level="debug")
