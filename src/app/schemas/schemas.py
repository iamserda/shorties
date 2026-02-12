from __future__ import annotations

from typing import Literal

from pydantic import AnyUrl
from pydantic import BaseModel


class NewUrlSubmissionModel(BaseModel):
    brand: str | None = None
    url: AnyUrl | str
    expires_on: str | None = None
    redirect_code: Literal[301, 302] = 302
    tags: list[str] | None = []
    notes: str | None = None

    def __str__(self):
        return f"brand: {self.brand}, url: {self.url}"


class GetURLRequestModel(BaseModel):
    key: str


class GetUrlResponseModel(BaseModel):
    key: str | None = None
    brand: str | None = None
    url: AnyUrl | str
    status: str | None = None
    message: str | None = None
    expires_on: str | None = None
    redirect_code: Literal[301, 302] = 302
    tags: list[str] | None = []
    notes: str | None = None
