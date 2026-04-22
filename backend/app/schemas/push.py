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


class PushPreviewResultDTO(AppSchema):
    success_count: int = Field(alias="successCount")
    failure_count: int = Field(alias="failureCount")


class PushLogDiagnosticsDTO(AppSchema):
    id: str
    notification_type: str = Field(alias="notificationType")
    status: str
    error_message: str | None = Field(alias="errorMessage", default=None)
    created_at: str = Field(alias="createdAt")


class PushDiagnosticsDTO(AppSchema):
    push_enabled: bool = Field(alias="pushEnabled")
    active_subscription_count: int = Field(alias="activeSubscriptionCount")
    last_success_at: str | None = Field(alias="lastSuccessAt", default=None)
    last_failure_at: str | None = Field(alias="lastFailureAt", default=None)
    last_failure_reason: str | None = Field(alias="lastFailureReason", default=None)
    recent_logs: list[PushLogDiagnosticsDTO] = Field(alias="recentLogs")
