from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import CheckInConfig, Owner
from app.repositories import notification as notification_repo
from app.repositories.emergency_chain import list_ordered_contacts
from app.services.auth import generate_id
from app.services.check_in import EscalationMode, compute_escalation_state
from app.services.email import (
    build_escalation_email,
    build_reminder_email,
    send_email,
)

logger = logging.getLogger(__name__)

CONTACT_NOTIFY_GAP = timedelta(minutes=5)


def dispatch_notifications(session: Session) -> None:
    """Check all owners with check-in configs and send notifications if needed."""
    configs = session.scalars(select(CheckInConfig)).all()

    for config in configs:
        try:
            _process_owner(session, config)
        except Exception:
            logger.exception("dispatch failed owner_id=%s", config.owner_id)


def _process_owner(session: Session, config: CheckInConfig) -> None:
    mode, _deadline = compute_escalation_state(config)

    if mode == EscalationMode.PENDING:
        _send_reminder(session, config)

    if mode == EscalationMode.ESCALATED:
        _send_escalation_alerts(session, config)


def _send_reminder(session: Session, config: CheckInConfig) -> None:
    existing = notification_repo.find_reminder_for_cycle(
        session,
        config.owner_id,
        config.next_scheduled_at.isoformat(),
    )
    if existing is not None:
        return

    owner = session.scalar(select(Owner).where(Owner.id == config.owner_id))
    if owner is None:
        return

    settings = get_settings()
    subject, body = build_reminder_email(owner.display_name, settings.app_url)

    status = "sent"
    error_msg = None
    try:
        send_email(to=owner.email, subject=subject, body=body)
    except Exception as exc:
        status = "failed"
        error_msg = str(exc)[:500]

    notification_repo.create_notification_log(
        session,
        log_id=generate_id(),
        owner_id=config.owner_id,
        recipient_email=owner.email,
        notification_type="reminder",
        status=status,
        error_message=error_msg,
    )
    session.commit()


def _send_escalation_alerts(session: Session, config: CheckInConfig) -> None:
    from app.repositories.check_in import get_active_escalation

    active_escalation = get_active_escalation(session, config.owner_id)
    if active_escalation is None:
        return

    contacts = list_ordered_contacts(session, config.owner_id)
    if not contacts:
        return

    alerts = notification_repo.find_alerts_for_escalation(session, active_escalation.id)

    next_index = len(alerts)
    if next_index >= len(contacts):
        return

    if alerts:
        last_alert_time = alerts[-1].created_at
        if last_alert_time.tzinfo is None:
            last_alert_time = last_alert_time.replace(tzinfo=UTC)
        if datetime.now(UTC) - last_alert_time < CONTACT_NOTIFY_GAP:
            return

    contact, _entry = contacts[next_index]
    settings = get_settings()

    owner = session.scalar(select(Owner).where(Owner.id == config.owner_id))
    owner_name = owner.display_name if owner else "Unbekannt"

    subject, body = build_escalation_email(
        contact_name=contact.name,
        owner_name=owner_name,
        app_url=settings.app_url,
        position=next_index + 1,
        total=len(contacts),
    )

    status = "sent"
    error_msg = None
    try:
        send_email(to=contact.email, subject=subject, body=body)
    except Exception as exc:
        status = "failed"
        error_msg = str(exc)[:500]

    notification_repo.create_notification_log(
        session,
        log_id=generate_id(),
        owner_id=config.owner_id,
        recipient_email=contact.email,
        notification_type="escalation_alert",
        status=status,
        escalation_event_id=active_escalation.id,
        error_message=error_msg,
    )
    session.commit()
