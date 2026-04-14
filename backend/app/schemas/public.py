from pydantic import Field

from app.schemas.common import AppSchema


class ResponderAckRequest(AppSchema):
    email: str
    name: str | None = Field(default=None)


class ResponderAckResponse(AppSchema):
    success: bool
