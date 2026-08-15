from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(
    prefix="/healthz",
    tags=["Health Check"],
)


@router.get("/")
async def health_check():
    """
    Health check endpoint to verify if the API is running.
    Returns a simple JSON response indicating the status of the API.
    """
    return {"status": "alive"}
