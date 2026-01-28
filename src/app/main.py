from fastapi import FastAPI

app = FastAPI()

@app.get("/healthz")
def healthz()->dict:
    return {"status": "alive"}

if __name__ == "__main__":
    import uvicorn
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    uvicorn.run(app, host=HOST, port=PORT, log_level="debug")