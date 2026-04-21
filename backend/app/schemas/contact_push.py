from pydantic import Field

from app.schemas.common import AppSchema


class ContactPushSubscribeRequest(AppSchema):
    email: str
    endpoint: str
    p256dh: str
    auth: str
    user_agent: str | None = Field(alias="userAgent", default=None)


class ContactPushUnsubscribeRequest(AppSchema):
    endpoint: str
