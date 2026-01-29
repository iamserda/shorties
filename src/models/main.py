from pydantic import BaseModel

class CreateUrl(BaseModel):
    url: str

class UrlResponse(BaseModel):
    key: str
    url: str | None = None