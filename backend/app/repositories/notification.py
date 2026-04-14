from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from app.db.models import NotificationLog


def find_reminder_for_cycle(
    session: Session,
    owner_id: str,
    cycle_start_iso: str,
) -> NotificationLog | None:
    """Check if a reminder was already sent for this overdue cycle."""
    from datetime import datetime

    cycle_start = datetime.fromisoformat(cycle_start_iso)
    statement: Select[tuple[NotificationLog]] = select(NotificationLog).where(
        NotificationLog.owner_id == owner_id,
        NotificationLog.notification_type == "reminder",
        NotificationLog.created_at >= cycle_start,
    )
    return session.scalar(statement)


def find_alerts_for_escalation(
    session: Session,
    escalation_event_id: str,
) -> list[NotificationLog]:
    statement = (
        select(NotificationLog)
        .where(
            NotificationLog.escalation_event_id == escalation_event_id,
            NotificationLog.notification_type == "escalation_alert",
        )
        .order_by(NotificationLog.created_at)
    )
    return list(session.scalars(statement))


def create_notification_log(
    session: Session,
    log_id: str,
    owner_id: str,
    recipient_email: str,
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
