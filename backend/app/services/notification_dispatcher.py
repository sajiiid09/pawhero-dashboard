from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import (
    CheckInConfig,
    NotificationChannel,
    NotificationType,
    Owner,
    Pet,
)
from app.repositories import notification as notification_repo
from app.repositories.check_in import create_escalation_event, get_active_escalation
from app.repositories.emergency_chain import list_ordered_contacts
from app.repositories.pets import list_pets
from app.services.auth import generate_id
from app.services.check_in import EscalationMode, compute_escalation_state
from app.services.email import (
    build_emergency_contact_escalation_email,
    build_owner_escalation_email,
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
    mode, deadline = compute_escalation_state(config)

    if mode == EscalationMode.PENDING:
        _send_pending_notifications(session, config)
        return

    if mode == EscalationMode.ESCALATED:
        _send_escalation_alerts(session, config, deadline)


def _send_pending_notifications(session: Session, config: CheckInConfig) -> None:
    owner = _get_owner(session, config.owner_id)
    if owner is None:
        return

    cycle_key = config.next_scheduled_at.isoformat()
    did_change = False

    if (
        config.push_enabled
        and _find_cycle_notification(
            session,
            owner_id=config.owner_id,
            cycle_key=cycle_key,
            notification_type=NotificationType.OWNER_REMINDER,
            channel=NotificationChannel.PUSH,
        )
        is None
    ):
        _log_notification(
            session,
            owner_id=config.owner_id,
            recipient_email=owner.email,
            channel=NotificationChannel.PUSH,
            notification_type=NotificationType.OWNER_REMINDER,
            status="sent",
        )
        did_change = True

    if (
        config.email_enabled
        and _find_cycle_notification(
            session,
            owner_id=config.owner_id,
            cycle_key=cycle_key,
            notification_type=NotificationType.OWNER_REMINDER,
            channel=NotificationChannel.EMAIL,
        )
        is None
    ):
        settings = get_settings()
        subject, body = build_reminder_email(
            owner.display_name,
            settings.app_url,
            include_push_note=config.push_enabled,
        )
        _send_email_notification(
            session,
            owner_id=config.owner_id,
            recipient_email=owner.email,
            channel=NotificationChannel.EMAIL,
            notification_type=NotificationType.OWNER_REMINDER,
            subject=subject,
            body=body,
        )
        did_change = True

    if did_change:
        session.commit()


def _send_escalation_alerts(
    session: Session,
    config: CheckInConfig,
    deadline: datetime | None,
) -> None:
    owner = _get_owner(session, config.owner_id)
    primary_pet = _get_primary_pet(session, config.owner_id)
    if owner is None:
        return

    active_escalation = _ensure_active_escalation(session, config.owner_id, deadline)
    settings = get_settings()
    public_profile_url = _get_public_profile_url(session, primary_pet, settings.app_url)
    did_change = False

    if primary_pet is not None and public_profile_url is not None:
        owner_alerts = notification_repo.find_notifications_for_escalation(
            session,
            active_escalation.id,
            notification_type=NotificationType.OWNER_ESCALATION,
            channel=NotificationChannel.EMAIL,
        )
        if not owner_alerts:
            subject, body = build_owner_escalation_email(
                owner_name=owner.display_name,
                pet_name=primary_pet.name,
                app_url=settings.app_url,
                public_profile_url=public_profile_url,
            )
            _send_email_notification(
                session,
                owner_id=config.owner_id,
                escalation_event_id=active_escalation.id,
                recipient_email=owner.email,
                channel=NotificationChannel.EMAIL,
                notification_type=NotificationType.OWNER_ESCALATION,
                subject=subject,
                body=body,
            )
            did_change = True

    contacts = list_ordered_contacts(session, config.owner_id)
    if not contacts or primary_pet is None or public_profile_url is None:
        if did_change:
            session.commit()
        return

    contact_alerts = notification_repo.find_notifications_for_escalation(
        session,
        active_escalation.id,
        notification_type=NotificationType.EMERGENCY_CONTACT_ESCALATION,
        channel=NotificationChannel.EMAIL,
    )
    next_index = len(contact_alerts)
    if next_index >= len(contacts):
        if did_change:
            session.commit()
        return

    if contact_alerts and not _is_gap_elapsed(contact_alerts[-1].created_at):
        if did_change:
            session.commit()
        return

    contact, _entry = contacts[next_index]
    subject, body = build_emergency_contact_escalation_email(
        contact_name=contact.name,
        owner_name=owner.display_name,
        pet_name=primary_pet.name,
        public_profile_url=public_profile_url,
        position=next_index + 1,
        total=len(contacts),
    )
    _send_email_notification(
        session,
        owner_id=config.owner_id,
        escalation_event_id=active_escalation.id,
        recipient_email=contact.email,
        channel=NotificationChannel.EMAIL,
        notification_type=NotificationType.EMERGENCY_CONTACT_ESCALATION,
        subject=subject,
        body=body,
    )
    session.commit()


def _get_owner(session: Session, owner_id: str) -> Owner | None:
    return session.scalar(select(Owner).where(Owner.id == owner_id))


def _get_primary_pet(session: Session, owner_id: str) -> Pet | None:
    pets = list_pets(session, owner_id)
    return pets[0] if pets else None


def _ensure_active_escalation(
    session: Session,
    owner_id: str,
    deadline: datetime | None,
):
    active_escalation = get_active_escalation(session, owner_id)
    if active_escalation is not None:
        return active_escalation

    return create_escalation_event(
        session,
        event_id=generate_id(),
        owner_id=owner_id,
        started_at=deadline or datetime.now(UTC),
    )


def _get_public_profile_url(session: Session, pet: Pet | None, app_url: str) -> str | None:
    if pet is None:
        return None

    if not pet.emergency_access_token:
        pet.emergency_access_token = generate_id()
        session.flush()

    return f"{app_url}/s/{pet.emergency_access_token}"


def _find_cycle_notification(
    session: Session,
    *,
    owner_id: str,
    cycle_key: str,
    notification_type: NotificationType,
    channel: NotificationChannel,
):
    return notification_repo.find_notification_for_cycle(
        session,
        owner_id,
        cycle_key,
        notification_type=notification_type,
        channel=channel,
    )


def _is_gap_elapsed(created_at: datetime) -> bool:
    created = created_at if created_at.tzinfo is not None else created_at.replace(tzinfo=UTC)
    return datetime.now(UTC) - created >= CONTACT_NOTIFY_GAP


def _send_email_notification(
    session: Session,
    *,
    owner_id: str,
    recipient_email: str,
    channel: NotificationChannel,
    notification_type: NotificationType,
    subject: str,
    body: str,
    escalation_event_id: str | None = None,
) -> None:
    status = "sent"
    error_message = None

    try:
        send_email(to=recipient_email, subject=subject, body=body)
    except Exception as exc:
        status = "failed"
        error_message = str(exc)[:500]

    _log_notification(
        session,
        owner_id=owner_id,
        recipient_email=recipient_email,
        channel=channel,
        notification_type=notification_type,
        status=status,
        escalation_event_id=escalation_event_id,
        error_message=error_message,
    )


def _log_notification(
    session: Session,
    *,
    owner_id: str,
    recipient_email: str,
    channel: NotificationChannel,
    notification_type: NotificationType,
    status: str,
    escalation_event_id: str | None = None,
    error_message: str | None = None,
) -> None:
    notification_repo.create_notification_log(
        session,
        log_id=generate_id(),
        owner_id=owner_id,
        escalation_event_id=escalation_event_id,
        recipient_email=recipient_email,
        channel=channel,
        notification_type=notification_type,
        status=status,
        error_message=error_message,
    )
