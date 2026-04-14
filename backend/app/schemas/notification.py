from app.schemas.common import AppSchema


class NotificationLogDTO(AppSchema):
    id: str
    recipient_email: str
    notification_type: str
    status: str
    error_message: str | None
    created_at: str
