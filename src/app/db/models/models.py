from __future__ import annotations

from sqlmodel import Field
from sqlmodel import SQLModel


class ShortiLink(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    shorti_key: str = Field(index=True)
    shorti_url: str = Field(index=True)
    brand: str | None = Field(default=None)
