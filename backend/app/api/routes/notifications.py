from fastapi import APIRouter

from app.api.dependencies import DbSession, OwnerId
from app.db.models import NotificationLog
from app.repositories.notification import list_notification_logs
from app.schemas.notification import NotificationLogDTO

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=list[NotificationLogDTO])
def read_notifications(
    session: DbSession,
    owner_id: OwnerId,
) -> list[NotificationLogDTO]:
    logs = list_notification_logs(session, owner_id)
    return [_serialize(log) for log in logs]


def _serialize(log: NotificationLog) -> NotificationLogDTO:
    return NotificationLogDTO(
        id=log.id,
        recipient_email=log.recipient_email,
        notification_type=log.notification_type,
        status=log.status,
        error_message=log.error_message,
        created_at=log.created_at.isoformat(),
    )
