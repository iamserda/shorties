from __future__ import annotations

import logging
from typing import Annotated

from app.alnumgen import alnum_generator
from app.db.db_exceptions import DBEngineError
from app.db.db_exceptions import DBSessionError
from app.db.db_exceptions import EmptyDatabaseError
from app.db.models.models import LinkClickEvent
from app.db.models.models import ShortiLink
from app.db.models.models import utcnow
from app.db.session import get_db_session
from app.schemas.schemas import ClickEventResponseModel
from app.schemas.schemas import GetUrlResponseModel
from app.schemas.schemas import GetUrlsResponseModel
from app.schemas.schemas import LinkAnalyticsResponseModel
from app.schemas.schemas import NewUrlSubmissionModel
from app.schemas.schemas import UpdateUrlRequestModel
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi import status
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlmodel import col
from sqlmodel import select
from sqlmodel import Session

MAX_KEY_GENERATION_ATTEMPTS = 5
RECENT_CLICKS_LIMIT = 20

router = APIRouter(
    prefix="/links",
    tags=["Links"],
)

logger = logging.getLogger(__name__)

COMMON_ERROR_MESSAGE = "A server-side error occurred! It's has been logged for technical review. It will be reviewed ASAP by one our engineers."


def _not_found(shorti_key: str) -> HTTPException:
    return HTTPException(
        status_code=404,
        detail=f"No link found for key '{shorti_key}'.",
    )


def _to_response_model(link: ShortiLink) -> GetUrlResponseModel:
    return GetUrlResponseModel(
        key=link.shorti_key,
        url=link.shorti_url,
        brand=link.brand,
        redirect_code=link.redirect_code,
        hit_count=link.hit_count,
        created_at=link.created_at,
        updated_at=link.updated_at,
        last_accessed_at=link.last_accessed_at,
    )


def _get_link_or_404(
    session: Session, shorti_key: str, *, include_deleted: bool = False
) -> ShortiLink:
    statement = select(ShortiLink).where(ShortiLink.shorti_key == shorti_key)
    if not include_deleted:
        statement = statement.where(col(ShortiLink.deleted_at).is_(None))
    link = session.exec(statement).first()
    if link is None:
        raise _not_found(shorti_key)
    return link


@router.get("/", response_model=GetUrlsResponseModel, summary="Get all links")
async def get_all_links(
    session: Annotated[Session, Depends(get_db_session)],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, le=20),
    include_deleted: bool = Query(
        default=False,
        description="Admin flag: include soft-deleted links in the results.",
    ),
) -> GetUrlsResponseModel:
    empty_db_error = {
        "name": "empty-database-error",
        "description": "Our database is currently empty! Please create a new link via the API enpoints for creating new links and try again. See our documentation for more information.",
    }
    try:
        select_statement = select(ShortiLink)
        if not include_deleted:
            select_statement = select_statement.where(
                col(ShortiLink.deleted_at).is_(None)
            )
        select_statement = select_statement.offset(offset).limit(limit)
        new_urls = [
            _to_response_model(shorti)
            for shorti in session.exec(statement=select_statement).all()
        ]
        results = GetUrlsResponseModel(urls=new_urls)
        if not results.urls:
            raise EmptyDatabaseError(empty_db_error)
    except EmptyDatabaseError as empty_db_err:
        logger.info(
            f"error: {empty_db_err.description}",
            exc_info=True,
        )
        return GetUrlsResponseModel(urls=[])
    except DBSessionError as db_session_err:
        logger.exception(
            f"error: {db_session_err}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "type": db_session_err.__class__.__name__,
                    "description": db_session_err.description,
                    "status-code": 500,
                    "message": COMMON_ERROR_MESSAGE,
                }
            },
        )
    except DBEngineError as db_engine_err:
        logger.exception(
            f"error: {db_engine_err}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "type": db_engine_err.__class__.__name__,
                    "description": db_engine_err.description,
                    "status-code": 500,
                    "message": COMMON_ERROR_MESSAGE,
                }
            },
        )
    except HTTPException as httpErr:
        logger.info(
            f"A generic HTTP Exception occurred while getting links from database: {httpErr}"
        )
        raise
    except Exception as app_exception:
        logger.exception(
            f"An unexpected error occurred while getting links from database: {app_exception}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=COMMON_ERROR_MESSAGE,
        )
    return results


@router.post(
    "/",
    response_model=GetUrlResponseModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new short link",
)
async def create_link(
    submission: NewUrlSubmissionModel,
    session: Annotated[Session, Depends(get_db_session)],
) -> GetUrlResponseModel:
    try:
        for _ in range(MAX_KEY_GENERATION_ATTEMPTS):
            shorti_key = alnum_generator()
            link = ShortiLink(
                shorti_key=shorti_key,
                shorti_url=str(submission.url),
                brand=submission.brand,
                redirect_code=submission.redirect_code,
            )
            session.add(link)
            try:
                session.commit()
            except IntegrityError:
                # shorti_key collided with an existing row; retry with a new key.
                session.rollback()
                continue
            session.refresh(link)
            return _to_response_model(link)
        raise HTTPException(
            status_code=500,
            detail="Could not generate a unique short link key. Please try again.",
        )
    except HTTPException:
        raise
    except Exception as app_exception:
        logger.exception(
            f"An unexpected error occurred while creating a link: {app_exception}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=COMMON_ERROR_MESSAGE,
        )


@router.get(
    "/{shorti_key}",
    response_model=GetUrlResponseModel,
    summary="Get a single link",
)
async def get_link(
    shorti_key: str,
    session: Annotated[Session, Depends(get_db_session)],
) -> GetUrlResponseModel:
    try:
        link = _get_link_or_404(session, shorti_key)
        return _to_response_model(link)
    except HTTPException:
        raise
    except Exception as app_exception:
        logger.exception(
            f"An unexpected error occurred while fetching link '{shorti_key}': {app_exception}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=COMMON_ERROR_MESSAGE,
        )


@router.put(
    "/{shorti_key}",
    response_model=GetUrlResponseModel,
    summary="Update an existing short link",
)
async def update_link(
    shorti_key: str,
    update: UpdateUrlRequestModel,
    session: Annotated[Session, Depends(get_db_session)],
) -> GetUrlResponseModel:
    try:
        link = _get_link_or_404(session, shorti_key)
        if update.url is not None:
            link.shorti_url = str(update.url)
        if update.brand is not None:
            link.brand = update.brand
        if update.redirect_code is not None:
            link.redirect_code = update.redirect_code
        link.updated_at = utcnow()
        session.add(link)
        session.commit()
        session.refresh(link)
        return _to_response_model(link)
    except HTTPException:
        raise
    except Exception as app_exception:
        logger.exception(
            f"An unexpected error occurred while updating link '{shorti_key}': {app_exception}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=COMMON_ERROR_MESSAGE,
        )


@router.delete(
    "/{shorti_key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a short link",
)
async def delete_link(
    shorti_key: str,
    session: Annotated[Session, Depends(get_db_session)],
) -> None:
    try:
        link = _get_link_or_404(session, shorti_key)
        now = utcnow()
        link.deleted_at = now
        link.updated_at = now
        session.add(link)
        session.commit()
    except HTTPException:
        raise
    except Exception as app_exception:
        logger.exception(
            f"An unexpected error occurred while deleting link '{shorti_key}': {app_exception}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=COMMON_ERROR_MESSAGE,
        )


@router.get(
    "/{shorti_key}/visit",
    summary="Resolve a short link and redirect to its target URL",
)
async def visit_link(
    shorti_key: str,
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
) -> RedirectResponse:
    try:
        link = _get_link_or_404(session, shorti_key)
        now = utcnow()
        link.hit_count += 1
        link.last_accessed_at = now
        session.add(link)
        session.add(
            LinkClickEvent(
                shorti_link_id=link.id,
                clicked_at=now,
                referrer=request.headers.get("referer"),
                user_agent=request.headers.get("user-agent"),
                ip_address=request.client.host if request.client else None,
            )
        )
        session.commit()
        return RedirectResponse(url=link.shorti_url, status_code=link.redirect_code)
    except HTTPException:
        raise
    except Exception as app_exception:
        logger.exception(
            f"An unexpected error occurred while visiting link '{shorti_key}': {app_exception}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=COMMON_ERROR_MESSAGE,
        )


@router.get(
    "/{shorti_key}/analytics",
    response_model=LinkAnalyticsResponseModel,
    summary="Get hit-count and recent click analytics for a link",
)
async def get_link_analytics(
    shorti_key: str,
    session: Annotated[Session, Depends(get_db_session)],
) -> LinkAnalyticsResponseModel:
    try:
        link = _get_link_or_404(session, shorti_key)
        clicks_statement = (
            select(LinkClickEvent)
            .where(LinkClickEvent.shorti_link_id == link.id)
            .order_by(col(LinkClickEvent.clicked_at).desc())
            .limit(RECENT_CLICKS_LIMIT)
        )
        recent_clicks = [
            ClickEventResponseModel(
                clicked_at=click.clicked_at,
                referrer=click.referrer,
                user_agent=click.user_agent,
            )
            for click in session.exec(clicks_statement).all()
        ]
        return LinkAnalyticsResponseModel(
            key=link.shorti_key,
            hit_count=link.hit_count,
            created_at=link.created_at,
            updated_at=link.updated_at,
            last_accessed_at=link.last_accessed_at,
            recent_clicks=recent_clicks,
        )
    except HTTPException:
        raise
    except Exception as app_exception:
        logger.exception(
            f"An unexpected error occurred while fetching analytics for link '{shorti_key}': {app_exception}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=COMMON_ERROR_MESSAGE,
        )
