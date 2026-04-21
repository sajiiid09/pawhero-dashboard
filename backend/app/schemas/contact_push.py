from pydantic import Field

from app.schemas.common import AppSchema


class ContactPushSubscribeRequest(AppSchema):
    email: str
    endpoint: str
    p256dh: str
    auth: str
    user_agent: str | None = Field(alias="userAgent", default=None)


class ContactPushStatusRequest(AppSchema):
    email: str


class ContactPushUnsubscribeRequest(AppSchema):
    email: str
    endpoint: str


class ContactPushStatusDTO(AppSchema):
    email: str
    endpoints: list[str]
