from __future__ import annotations

from datetime import datetime
from datetime import timezone

from sqlmodel import Field
from sqlmodel import SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ShortiLink(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    shorti_key: str = Field(index=True, unique=True)
    shorti_url: str = Field(index=True)
    brand: str | None = Field(default=None)
    redirect_code: int = Field(default=307)

    # Analytics
    hit_count: int = Field(default=0)
    last_accessed_at: datetime | None = Field(default=None)

    # Record lifecycle
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    deleted_at: datetime | None = Field(default=None, index=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class LinkClickEvent(SQLModel, table=True):
    """One row per recorded visit to a short link, for per-click analytics."""

    id: int | None = Field(default=None, primary_key=True)
    shorti_link_id: int = Field(foreign_key="shortilink.id", index=True)
    clicked_at: datetime = Field(default_factory=utcnow, index=True)
    referrer: str | None = Field(default=None)
    user_agent: str | None = Field(default=None)
    ip_address: str | None = Field(default=None)
