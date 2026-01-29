from fastapi import FastAPI
from models.main import CreateUrl, UrlResponse
from app.alnumgen import alnum_generator
from app.constants import KEY_MAX


app = FastAPI()
store = {}


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "alive"}


@app.get("/shorten")
def shorten() -> dict:
    key = alnum_generator()
    while not key.isalnum():
        key = alnum_generator()
    if store.get(key):
        return {"key": f"{key}", "url": store[key], "status": "success", "message": "A key was successfully generated"}

    return {"key": f"{key}", "url": None, "status": "success", "message": "A key was successfully generated"}


@app.post("/create")
def create_url():
    key = alnum_generator()
    while not 


if __name__ == "__main__":
    import uvicorn

    HOST: str = "0.0.0.0"
    PORT: int = 8001
    uvicorn.run(app, host=HOST, port=PORT, log_level="debug")
