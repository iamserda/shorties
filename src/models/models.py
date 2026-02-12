from __future__ import annotations

from sqlmodel import Field
from sqlmodel import SQLModel


class ShortiLink(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    shorti_key: str = Field(index=True)
    shorti_url: str = Field(index=True, default=None)
    user_submitted_url: str | None = Field(default=None)
    system_normalized_url: str | None = Field(default=None)
    status: str
    redirect_code: str | None = Field(default="302")
    brand: str | None = None
    tags: list[str] | None = []
    notes: str | None = None
    # time stamps
    created_by_user_id: str | None = None
    created_on: str | None = None
    last_updated_on: str | None = None
    expires_on: str | None = None
    total_click_count: int = 0
    recently_clicked_on: str | None = None


class ClickEvent(SQLModel):
    event_id: int | None = Field(primary_key=True, default=None)
    shortilink_id: int = Field(foreign_key=ShortiLink.id)
    timestamp: str | None = None
    visitor_id: str | None = None
    ip_hash: str | None = None
