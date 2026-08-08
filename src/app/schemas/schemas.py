from __future__ import annotations

from collections.abc import Sequence
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


class GetUrlsResponseModel(BaseModel):
    urls: Sequence[GetUrlResponseModel] | list[GetUrlResponseModel] = []
