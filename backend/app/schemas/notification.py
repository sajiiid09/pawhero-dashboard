from pydantic import Field

from app.schemas.common import AppSchema


class NotificationLogDTO(AppSchema):
    id: str
    recipient_email: str = Field(alias="recipientEmail")
    notification_type: str = Field(alias="notificationType")
    status: str
    error_message: str | None = Field(alias="errorMessage", default=None)
    created_at: str = Field(alias="createdAt")
