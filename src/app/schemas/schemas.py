from __future__ import annotations

from typing import Literal

from pydantic import AnyHttpUrl
from pydantic import BaseModel


class NewUrlSubmissionModel(BaseModel):
    shorti_brand: str | None = None
    shorti_url: AnyHttpUrl | str = "https://i.imgur.com/Secssr2.png"
    redirect_code: Literal[301, 302, 307] = 307

    def __str__(self):
        return f"brand: {self.shorti_brand}, url: {self.shorti_url}"


class GetURLRequestModel(BaseModel):
    shorti_key: str


class GetUrlResponseModel(BaseModel):
    shorti_key: str
    shorti_url: str
    shorti_brand: str | None
