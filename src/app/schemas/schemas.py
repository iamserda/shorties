from __future__ import annotations

from pydantic import BaseModel
from pydantic import HttpUrl


class NewUrlSubmissionModel(BaseModel):
    brand: str | None
    url: HttpUrl = HttpUrl("https://i.imgur.com/Secssr2.png")


class GetURLRequestModel(BaseModel):
    shorti_key: str


class GetUrlResponseModel(BaseModel):
    shorti_key: str
    shorti_url: HttpUrl
    shorti_brand: str | None
