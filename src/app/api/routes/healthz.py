from __future__ import annotations

import logging
from typing import Annotated

from app.db.session import get_db_session
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy import text
from sqlmodel import Session

router = APIRouter(
    prefix="/healthz",
    tags=["Health Check"],
)

logger = logging.getLogger(__name__)


@router.get("/")
async def health_check():
    """
    Liveness check: is the process up and serving requests at all?

    Deliberately does not touch the database — a liveness probe that
    depends on the DB means a brief DB blip gets a healthy process
    restarted for no reason. Use /healthz/ready for DB connectivity.
    """
    return {"status": "alive"}


@router.get("/ready")
async def readiness_check(session: Annotated[Session, Depends(get_db_session)]):
    """
    Readiness check: can this instance actually serve a DB-backed request?

    Runs a trivial query end-to-end through the real connection pool.
    A platform's readiness probe should stop routing traffic here on a
    503 without killing/restarting the instance the way a failed
    liveness check would.
    """
    try:
        session.execute(text("SELECT 1"))
    except Exception as db_error:
        logger.exception(f"readiness check failed: {db_error}", exc_info=True)
        raise HTTPException(status_code=503, detail={"status": "not ready"})
    return {"status": "ready"}
