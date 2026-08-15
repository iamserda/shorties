from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Literal

from pydantic import AnyHttpUrl
from pydantic import BaseModel


class NewUrlSubmissionModel(BaseModel):
    brand: str | None = None
    url: AnyHttpUrl = AnyHttpUrl("https://i.imgur.com/Secssr2.png")
    redirect_code: Literal[301, 302, 307] = 307

    def __str__(self):
        return f"brand: {self.brand}, url: {self.url}"


class GetURLRequestModel(BaseModel):
    shorti_key: str


class GetUrlResponseModel(BaseModel):
    key: str
    url: str
    brand: str | None
    redirect_code: int
    hit_count: int
    created_at: datetime
    updated_at: datetime
    last_accessed_at: datetime | None = None


class GetUrlsResponseModel(BaseModel):
    urls: Sequence[GetUrlResponseModel] | list[GetUrlResponseModel] = []


class UpdateUrlRequestModel(BaseModel):
    url: AnyHttpUrl | None = None
    brand: str | None = None
    redirect_code: Literal[301, 302, 307] | None = None


class ClickEventResponseModel(BaseModel):
    clicked_at: datetime
    referrer: str | None
    user_agent: str | None


class LinkAnalyticsResponseModel(BaseModel):
    key: str
    hit_count: int
    created_at: datetime
    updated_at: datetime
    last_accessed_at: datetime | None
    recent_clicks: (
        Sequence[ClickEventResponseModel] | list[ClickEventResponseModel]
    ) = []
