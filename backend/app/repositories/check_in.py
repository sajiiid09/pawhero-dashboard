from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from app.db.models import CheckInConfig, CheckInEvent, EscalationEvent


def get_check_in_config(session: Session, owner_id: str) -> CheckInConfig | None:
    statement = select(CheckInConfig).where(CheckInConfig.owner_id == owner_id)
    return session.scalar(statement)


def list_recent_check_in_events(
    session: Session, owner_id: str, limit: int = 3
) -> list[CheckInEvent]:
    statement: Select[tuple[CheckInEvent]] = (
        select(CheckInEvent)
        .where(CheckInEvent.owner_id == owner_id)
        .order_by(desc(CheckInEvent.acknowledged_at))
        .limit(limit)
    )
    return list(session.scalars(statement))


def list_check_in_events(session: Session, owner_id: str, limit: int = 20) -> list[CheckInEvent]:
    statement: Select[tuple[CheckInEvent]] = (
        select(CheckInEvent)
        .where(CheckInEvent.owner_id == owner_id)
        .order_by(desc(CheckInEvent.acknowledged_at))
        .limit(limit)
    )
    return list(session.scalars(statement))


def create_check_in_event(
    session: Session,
    owner_id: str,
    event_id: str,
    status: str,
    acknowledged_at: object,
    method: str,
) -> CheckInEvent:
    event = CheckInEvent(
        id=event_id,
        owner_id=owner_id,
        status=status,
        acknowledged_at=acknowledged_at,
        method=method,
    )
    session.add(event)
    session.flush()
    return event


def get_active_escalation(session: Session, owner_id: str) -> EscalationEvent | None:
    return session.scalar(
        select(EscalationEvent).where(
            EscalationEvent.owner_id == owner_id,
            EscalationEvent.resolved_at.is_(None),
        )
    )


def create_escalation_event(
    session: Session,
    event_id: str,
    owner_id: str,
    started_at: object,
) -> EscalationEvent:
    event = EscalationEvent(
        id=event_id,
        owner_id=owner_id,
        started_at=started_at,
    )
    session.add(event)
    session.flush()
    return event


def resolve_escalation(event: EscalationEvent, resolved_at: object) -> None:
    event.resolved_at = resolved_at
    session_flush(event)


def list_escalation_history(
    session: Session, owner_id: str, limit: int = 20
) -> list[EscalationEvent]:
    statement = (
        select(EscalationEvent)
        .where(EscalationEvent.owner_id == owner_id)
        .order_by(desc(EscalationEvent.started_at))
        .limit(limit)
    )
    return list(session.scalars(statement))


def session_flush(obj: object) -> None:
    from sqlalchemy import inspect

    session = inspect(obj).session
    if session is not None:
        session.flush()
