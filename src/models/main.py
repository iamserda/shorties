from pydantic import BaseModel, AnyUrl
from typing import Optional, Literal


class URLRequestModel(BaseModel):
    brand: Optional[str] | None = None
    url: AnyUrl
    expires_on: Optional[str] | None = None
    redirect_code: Literal[301, 302] = 302
    tags: Optional[list[str]] = []
    notes: Optional[str] | None = None

    def __str__(self):
        return f"brand: {self.brand}, url: {self.url}"

    # @classmethod
    # def __dict__(cls):
    #     return {"brand": cls.brand, "url": cls.url}


class UrlResponseModel(BaseModel):
    key: str | None = None
    brand: str | None = None
    url: AnyUrl | str | None = None
    status: str | None = None
    message: str | None = None
    expires_on: Optional[str] | None = None
    redirect_code: Literal[301, 302] = 302
    tags: Optional[list[str]] = []
    notes: Optional[str] | None = None


class ShortiLink(BaseModel):
    shorti_id: int
    key: str
    short_url: str

    user_submitted_url: AnyUrl | None = None
    system_normalized_url: str | None = None

    status: Literal["active", "disabled", "deleted", "pending_review"] = "active"
    redirect_code: Literal[301, 302] = 302

    brand: str | None = None
    tags: Optional[list[str]] = []
    notes: Optional[str] | None = None

    # time stamps
    created_by_user_id: str | None = None
    created_on: str | None = None
    last_updated_on: str | None = None
    expires_on: str | None = None

    total_click_count: int = 0
    recently_clicked_on: str | None = None


class ClickEvent(BaseModel):
    event_id: int
    shortilink_id: int
    timestamp: str | None = None
    visitor_id: str | None = None
    ip_hash: str | None = None