from pydantic import BaseModel

class URLModel(BaseModel):
    brand: str | None
    url: str

    def __str__(self):
        return f"brand: {self.brand}, url: {self.url}"


class UrlResponseModel(BaseModel):
    key: str
    brand: str | None
    url: str
    status: str
    message: str