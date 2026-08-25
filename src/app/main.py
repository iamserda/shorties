from __future__ import annotations

import logging
import os
from pathlib import Path

import uvicorn
from app.api.routes import health
from app.api.routes import links
from app.db.session import get_db_engine
from dotenv import load_dotenv
from fastapi import APIRouter
from fastapi import FastAPI
from sqlmodel import SQLModel


# environment configs
load_dotenv()

# Logging Configs
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

db_engine = get_db_engine(dev_mode=True)
if db_engine:
    SQLModel.metadata.create_all(db_engine)


# FASTAPI APP Config
app = FastAPI(title="Shorties App")
api_router = APIRouter()
api_version = f"/{os.getenv('API_VERSION')}"
if api_version not in set(["v1", "v2", "v3", "v4", "v5"]):
    api_version = "v1"


api_router.include_router(links.router)
api_router.include_router(health.router)
app.include_router(api_router, prefix=f"/{api_version}")
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
