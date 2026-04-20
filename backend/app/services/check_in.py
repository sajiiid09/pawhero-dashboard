from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum

from sqlalchemy.orm import Session

from app.db.models import CheckInConfig
from app.repositories.check_in import (
    create_check_in_event,
    create_escalation_event,
    get_active_escalation,
    get_check_in_config,
    resolve_escalation,
)
from app.schemas.check_in import (
    CheckInConfigDTO,
    CheckInConfigUpdateRequest,
    CheckInStatusDTO,
    EscalationEventDTO,
)
from app.services.auth import generate_id


class EscalationMode(StrEnum):
    NORMAL = "normal"
    PENDING = "pending"
    ESCALATED = "escalated"


def recompute_next_scheduled_at(interval_hours: int) -> datetime:
    return datetime.now(UTC) + timedelta(hours=interval_hours)


def save_check_in_config(
    session: Session,
    owner_id: str,
    payload: CheckInConfigUpdateRequest,
) -> CheckInConfig:
    config = get_check_in_config(session, owner_id)

    if config is None:
        config = CheckInConfig(owner_id=owner_id)
        session.add(config)

    config.interval_hours = payload.interval_hours
    config.escalation_delay_minutes = payload.escalation_delay_minutes
    config.push_enabled = payload.push_enabled
    config.email_enabled = payload.email_enabled
    config.next_scheduled_at = recompute_next_scheduled_at(payload.interval_hours)

    session.flush()
    session.refresh(config)
    return config


def serialize_check_in_config(config: CheckInConfig) -> CheckInConfigDTO:
    return CheckInConfigDTO.model_validate(
        {
            "interval_hours": config.interval_hours,
            "escalation_delay_minutes": config.escalation_delay_minutes,
            "push_enabled": config.push_enabled,
            "email_enabled": config.email_enabled,
            "next_scheduled_at": config.next_scheduled_at.isoformat(),
        }
    )


def compute_escalation_state(
    config: CheckInConfig | None,
) -> tuple[EscalationMode, datetime | None]:
    """Return (mode, escalation_deadline) from config timestamps.

    escalation_deadline is the moment escalation flips from pending to escalated,
    i.e. next_scheduled_at + escalation_delay_minutes.  None when mode is normal.
    """
    if config is None:
        return EscalationMode.NORMAL, None

    now = datetime.now(UTC)
    next_at = config.next_scheduled_at
    if next_at.tzinfo is None:
        next_at = next_at.replace(tzinfo=UTC)

    if now < next_at:
        return EscalationMode.NORMAL, None

    escalation_deadline = next_at + timedelta(minutes=config.escalation_delay_minutes)
    if now < escalation_deadline:
        return EscalationMode.PENDING, escalation_deadline

    return EscalationMode.ESCALATED, escalation_deadline


def build_escalation_display(
    mode: EscalationMode,
    deadline: datetime | None,
) -> dict:
    """Build escalation status dict for the dashboard response."""
    if mode == EscalationMode.PENDING:
        return {
            "mode": "pending",
            "title": "Check-In ausstehend",
            "description": "Bitte jetzt quittieren. Eskalation droht.",
            "escalation_deadline": deadline.isoformat() if deadline else None,
        }
    if mode == EscalationMode.ESCALATED:
        return {
            "mode": "escalated",
            "title": "Eskalation aktiv",
            "description": "Check-In wurde verpasst. Eskalationskette ausgeloest.",
            "escalation_deadline": deadline.isoformat() if deadline else None,
        }
    return {
        "mode": "normal",
        "title": "Normalbetrieb",
        "description": "Alle Systeme laufen. Keine aktive Eskalation.",
        "escalation_deadline": None,
    }


def acknowledge_check_in(
    session: Session,
    owner_id: str,
    method: str = "webapp",
) -> CheckInStatusDTO:
    config = get_check_in_config(session, owner_id)
    if config is None:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keine Check-In-Konfiguration vorhanden.",
        )

    now = datetime.now(UTC)
    mode, _ = compute_escalation_state(config)

    # If overdue, record a missed event for the cycle that was skipped.
    if mode != EscalationMode.NORMAL:
        missed_method = "push" if config.push_enabled else "email"
        create_check_in_event(
            session,
            owner_id=owner_id,
            event_id=generate_id(),
            status="missed",
            acknowledged_at=config.next_scheduled_at,
            method=missed_method,
        )

    # Resolve active escalation if one exists.
    active_escalation = get_active_escalation(session, owner_id)
    if active_escalation is not None:
        resolve_escalation(active_escalation, now)

    # Create acknowledged event.
    create_check_in_event(
        session,
        owner_id=owner_id,
        event_id=generate_id(),
        status="acknowledged",
        acknowledged_at=now,
        method=method,
    )

    # Reset the timer.
    config.next_scheduled_at = recompute_next_scheduled_at(config.interval_hours)
    session.flush()

    new_mode, new_deadline = compute_escalation_state(config)
    return CheckInStatusDTO(
        mode=new_mode,
        escalation_deadline=(new_deadline.isoformat() if new_deadline else None),
        next_check_in_at=config.next_scheduled_at.isoformat(),
    )


def get_check_in_status(session: Session, owner_id: str) -> CheckInStatusDTO | None:
    config = get_check_in_config(session, owner_id)
    if config is None:
        return None

    mode, deadline = compute_escalation_state(config)

    # Lazily create escalation event if escalated and none active.
    if mode == EscalationMode.ESCALATED:
        active = get_active_escalation(session, owner_id)
        if active is None:
            create_escalation_event(
                session,
                event_id=generate_id(),
                owner_id=owner_id,
                started_at=deadline or datetime.now(UTC),
            )
            session.flush()

    return CheckInStatusDTO(
        mode=mode,
        escalation_deadline=deadline.isoformat() if deadline else None,
        next_check_in_at=config.next_scheduled_at.isoformat(),
    )


def serialize_escalation_event(event: object) -> EscalationEventDTO:
    from app.db.models import EscalationEvent

    assert isinstance(event, EscalationEvent)
    return EscalationEventDTO(
        id=event.id,
        started_at=event.started_at.isoformat(),
        resolved_at=(event.resolved_at.isoformat() if event.resolved_at else None),
    )
