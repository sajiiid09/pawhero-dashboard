from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from app.db.models import NotificationLog


def find_notification_for_cycle(
    session: Session,
    owner_id: str,
    cycle_start_iso: str,
    notification_type: str,
    channel: str,
    statuses: tuple[str, ...] | None = None,
) -> NotificationLog | None:
    """Check if a notification was already sent for this overdue cycle."""
    from datetime import datetime

    cycle_start = datetime.fromisoformat(cycle_start_iso)
    statement: Select[tuple[NotificationLog]] = select(NotificationLog).where(
        NotificationLog.owner_id == owner_id,
        NotificationLog.notification_type == notification_type,
        NotificationLog.channel == channel,
        NotificationLog.created_at >= cycle_start,
    )
    if statuses:
        statement = statement.where(NotificationLog.status.in_(statuses))
    return session.scalar(statement)


def find_notifications_for_escalation(
    session: Session,
    escalation_event_id: str,
    *,
    notification_type: str | None = None,
    channel: str | None = None,
    statuses: tuple[str, ...] | None = None,
) -> list[NotificationLog]:
    filters = [NotificationLog.escalation_event_id == escalation_event_id]
    if notification_type is not None:
        filters.append(NotificationLog.notification_type == notification_type)
    if channel is not None:
        filters.append(NotificationLog.channel == channel)
    if statuses is not None:
        filters.append(NotificationLog.status.in_(statuses))

    statement = select(NotificationLog).where(*filters).order_by(NotificationLog.created_at)
    return list(session.scalars(statement))


def create_notification_log(
    session: Session,
    log_id: str,
    owner_id: str,
    recipient_email: str,
    channel: str,
    notification_type: str,
    status: str,
    escalation_event_id: str | None = None,
    error_message: str | None = None,
) -> NotificationLog:
    log = NotificationLog(
        id=log_id,
        owner_id=owner_id,
        escalation_event_id=escalation_event_id,
        recipient_email=recipient_email,
        channel=channel,
        notification_type=notification_type,
        status=status,
        error_message=error_message,
    )
    session.add(log)
    session.flush()
    return log


def list_notification_logs(
    session: Session,
    owner_id: str,
    limit: int = 50,
) -> list[NotificationLog]:
    statement = (
        select(NotificationLog)
        .where(NotificationLog.owner_id == owner_id)
        .order_by(desc(NotificationLog.created_at))
        .limit(limit)
    )
    return list(session.scalars(statement))
