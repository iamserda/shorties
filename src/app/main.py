from fastapi import FastAPI
from models.main import CreateUrl, UrlResponse
from app.alnumgen import alnum_generator
from app.constants import KEY_MAX


app = FastAPI()
store = {
    "goog": "https://www.google.com",
    "meta": "https://www.facebook.com",
    "twttr": "https://www.twitter.com",
    "lknd": "https://www.linkedin.com",
    "github": "https://www.github.com",
    "reddit": "https://www.reddit.com",
    "youtub": "https://www.youtube.com",
    "insta": "https://www.instagram.com",
    "microsoft": "https://www.microsoft.com",
    "apple": "https://www.apple.com",
}


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "alive"}


@app.get("/redirect/{key}")
def get_url(key: str) -> dict:
    try:
        if not key:
            raise ValueError("Invalid, user did not provide a key.")
        if not isinstance(key, str):
            raise TypeError("The key provided is not of a valid type. Key must be a str.")
        if key in store:
            return {"key": f"{key}", "url": store.get(key), "status": "success", "message": "success: url was found!"}
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


@app.post("/create/{new_url}")
def create_url(new_url) -> dict:
    key = alnum_generator()
    try:
        while key in store:
            key = alnum_generator()
        store[key] = new_url
        if key in store:
            return {
                "key": f"{key}",
                "url": store[key],
                "status": "success",
                "message": "A key was successfully generated",
            }
        else:
            return {"key": f"{key}", "url": None, "status": "failed", "message": "A key was successfully generated"}
    except KeyError as err:
        print(err)  # todo: logg
        pass


if __name__ == "__main__":
    import uvicorn
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    uvicorn.run(app, host=HOST, port=PORT, log_level="debug")
