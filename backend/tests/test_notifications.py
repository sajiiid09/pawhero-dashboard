from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select

from app.db.models import (
    CheckInConfig,
    EscalationEvent,
    NotificationLog,
    NotificationType,
    ResponderAcknowledgment,
)
from app.db.session import get_session_factory
from app.repositories.emergency_chain import list_ordered_contacts
from app.services.notification_dispatcher import CONTACT_NOTIFY_GAP, dispatch_notifications


def _reset_notification_flow_state(session) -> None:
    session.execute(delete(NotificationLog).where(NotificationLog.owner_id == "owner-demo"))
    session.execute(delete(ResponderAcknowledgment))
    session.execute(delete(EscalationEvent).where(EscalationEvent.owner_id == "owner-demo"))
    session.commit()


def test_pending_dispatch_creates_push_and_email_once(monkeypatch, test_database_url: str):
    del test_database_url
    deliveries: list[tuple[str, str, str]] = []

    def fake_send_email(*, to: str, subject: str, body: str) -> None:
        deliveries.append((to, subject, body))

    monkeypatch.setattr("app.services.notification_dispatcher.send_email", fake_send_email)

    session = get_session_factory()()
    try:
        _reset_notification_flow_state(session)
        config = session.scalar(select(CheckInConfig).where(CheckInConfig.owner_id == "owner-demo"))
        assert config is not None
        config.next_scheduled_at = datetime.now(UTC) - timedelta(minutes=5)
        config.escalation_delay_minutes = 30
        session.commit()

        dispatch_notifications(session)
        dispatch_notifications(session)

        logs = list(
            session.scalars(
                select(NotificationLog)
                .where(NotificationLog.owner_id == "owner-demo")
                .order_by(NotificationLog.created_at)
            )
        )
        reminder_logs = [
            log
            for log in logs
            if log.notification_type == NotificationType.OWNER_REMINDER
        ]

        assert len(reminder_logs) == 2
        assert sorted(log.channel for log in reminder_logs) == ["email", "push"]
        assert len(deliveries) == 1
        assert deliveries[0][0] == "demo@pfoten-held.de"
    finally:
        session.close()


def test_escalation_dispatch_emails_owner_then_contacts_with_public_link(
    monkeypatch,
    test_database_url: str,
):
    del test_database_url
    deliveries: list[tuple[str, str, str]] = []

    def fake_send_email(*, to: str, subject: str, body: str) -> None:
        deliveries.append((to, subject, body))

    monkeypatch.setattr("app.services.notification_dispatcher.send_email", fake_send_email)

    session = get_session_factory()()
    try:
        _reset_notification_flow_state(session)
        config = session.scalar(select(CheckInConfig).where(CheckInConfig.owner_id == "owner-demo"))
        assert config is not None
        config.next_scheduled_at = datetime.now(UTC) - timedelta(minutes=45)
        config.escalation_delay_minutes = 15
        session.commit()

        contacts = list_ordered_contacts(session, "owner-demo")
        expected_first_email = contacts[0][0].email
        expected_second_email = contacts[1][0].email

        dispatch_notifications(session)

        logs = list(
            session.scalars(
                select(NotificationLog)
                .where(NotificationLog.owner_id == "owner-demo")
                .order_by(NotificationLog.created_at)
            )
        )
        owner_alerts = [
            log
            for log in logs
            if log.notification_type == NotificationType.OWNER_ESCALATION
        ]
        contact_alerts = [
            log
            for log in logs
            if log.notification_type == NotificationType.EMERGENCY_CONTACT_ESCALATION
        ]

        assert len(owner_alerts) == 1
        assert len(contact_alerts) == 1
        assert deliveries[0][0] == "demo@pfoten-held.de"
        assert deliveries[1][0] == expected_first_email
        assert "/s/token-bello-public" in deliveries[0][2]
        assert "/s/token-bello-public" in deliveries[1][2]

        dispatch_notifications(session)
        logs_after_second_run = list(
            session.scalars(
                select(NotificationLog)
                .where(NotificationLog.owner_id == "owner-demo")
                .order_by(NotificationLog.created_at)
            )
        )
        assert len(
            [
                log
                for log in logs_after_second_run
                if log.notification_type == NotificationType.EMERGENCY_CONTACT_ESCALATION
            ]
        ) == 1

        first_contact_log = contact_alerts[0]
        first_contact_log.created_at = datetime.now(UTC) - CONTACT_NOTIFY_GAP - timedelta(minutes=1)
        session.commit()

        dispatch_notifications(session)

        final_logs = list(
            session.scalars(
                select(NotificationLog)
                .where(NotificationLog.owner_id == "owner-demo")
                .order_by(NotificationLog.created_at)
            )
        )
        final_contact_alerts = [
            log
            for log in final_logs
            if log.notification_type == NotificationType.EMERGENCY_CONTACT_ESCALATION
        ]
        assert len(final_contact_alerts) == 2
        assert deliveries[-1][0] == expected_second_email
    finally:
        session.close()


def test_public_acknowledgment_logs_owner_notification(client, auth_headers, monkeypatch):
    deliveries: list[tuple[str, str, str]] = []

    def fake_send_email(*, to: str, subject: str, body: str) -> None:
        deliveries.append((to, subject, body))

    monkeypatch.setattr("app.services.notification_dispatcher.send_email", fake_send_email)
    monkeypatch.setattr("app.api.routes.public.send_email", fake_send_email)

    session = get_session_factory()()
    try:
        _reset_notification_flow_state(session)
        config = session.scalar(select(CheckInConfig).where(CheckInConfig.owner_id == "owner-demo"))
        assert config is not None
        config.next_scheduled_at = datetime.now(UTC) - timedelta(minutes=45)
        config.escalation_delay_minutes = 15
        session.commit()

        dispatch_notifications(session)
    finally:
        session.close()

    response = client.post(
        "/public/emergency-profile/token-bello-public/acknowledge",
        json={"email": "helper@example.com", "name": "Helfer"},
    )
    assert response.status_code == 200

    session = get_session_factory()()
    try:
        logs = list(
            session.scalars(
                select(NotificationLog)
                .where(NotificationLog.owner_id == "owner-demo")
                .order_by(NotificationLog.created_at)
            )
        )
        ack_logs = [
            log
            for log in logs
            if log.notification_type == NotificationType.RESPONDER_ACKNOWLEDGMENT
        ]

        assert len(ack_logs) == 1
        assert ack_logs[0].recipient_email == "demo@pfoten-held.de"
        assert deliveries[-1][0] == "demo@pfoten-held.de"

        summary = client.get("/dashboard/summary", headers=auth_headers)
        assert summary.status_code == 200
        assert summary.json()["escalationStatus"]["title"] == "Hilfe bestaetigt"
    finally:
        session.close()
