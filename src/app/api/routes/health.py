from __future__ import annotations

from app.db.models.models import ShortiLink
from app.db.session import get_session
from dotenv import load_dotenv
from fastapi import APIRouter
from fastapi import Depends
from sqlmodel import select

load_dotenv()

router = APIRouter(prefix="/healthz")


# Routes + Route Handling
@router.get("/")
async def healthz(session=Depends(get_session)) -> dict:
    select_statement = select(ShortiLink)
    result = session.exec(select_statement).first()
    if result:
        return {"status": "alive", "db-connection": "alive"}
    return {"status": "alive", "db-connection": "unknown"}
