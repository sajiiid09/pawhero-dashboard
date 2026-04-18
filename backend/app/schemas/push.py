from pydantic import Field

from app.schemas.common import AppSchema


class SavePushSubscriptionRequest(AppSchema):
    endpoint: str
    p256dh: str = Field(alias="p256dh")
    auth: str = Field(alias="auth")
    user_agent: str | None = Field(alias="userAgent", default=None)


class PushSubscriptionDTO(AppSchema):
    id: str
    endpoint: str
    user_agent: str | None = Field(alias="userAgent")
    created_at: str = Field(alias="createdAt")
    last_seen_at: str = Field(alias="lastSeenAt")


class TestPushResultDTO(AppSchema):
    success_count: int = Field(alias="successCount")
    failure_count: int = Field(alias="failureCount")
