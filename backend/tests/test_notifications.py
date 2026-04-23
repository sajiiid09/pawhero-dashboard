import re
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
from app.services.check_in import acknowledge_check_in
from app.services.notification_dispatcher import CONTACT_NOTIFY_GAP, dispatch_notifications
from app.services.push import PushResult


def _fake_push_success(*args, **kwargs):
    return PushResult(success_count=1, failure_count=0)


def extract_public_check_in_url(message_body: str) -> str:
    match = re.search(r"https?://[^\s]+/c/[^\s]+", message_body)
    assert match is not None
    return match.group(0)


def _reset_notification_flow_state(session) -> None:
    session.execute(delete(NotificationLog).where(NotificationLog.owner_id == "owner-demo"))
    session.execute(delete(ResponderAcknowledgment))
    session.execute(delete(EscalationEvent).where(EscalationEvent.owner_id == "owner-demo"))
    session.commit()


def test_pending_dispatch_creates_push_and_email_once(monkeypatch, test_database_url: str):
    del test_database_url
    deliveries: list[tuple[str, str, str]] = []
    push_deliveries: list[tuple[str, str, str, str]] = []

    def fake_send_email(*, to: str, subject: str, body: str) -> None:
        deliveries.append((to, subject, body))

    def fake_send_push(session, owner_id, title, body, url="/dashboard", **kwargs):
        del session, body
        push_deliveries.append((owner_id, title, url, kwargs["category"]))
        return PushResult(success_count=1, failure_count=0)

    monkeypatch.setattr("app.services.notification_dispatcher.send_email", fake_send_email)
    monkeypatch.setattr("app.services.notification_dispatcher.send_push_to_owner", fake_send_push)

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
            log for log in logs if log.notification_type == NotificationType.OWNER_REMINDER
        ]

        assert len(reminder_logs) == 2
        assert sorted(log.channel for log in reminder_logs) == ["email", "push"]
        assert len(deliveries) == 1
        assert deliveries[0][0] == "demo@pfoten-held.de"
        assert len(push_deliveries) == 1
        expected_url = extract_public_check_in_url(deliveries[0][2])
        assert push_deliveries[0][2] == expected_url
        assert push_deliveries[0][3] == "check_in"
    finally:
        session.close()


def test_escalation_dispatch_emails_owner_then_contacts_with_public_link(
    monkeypatch,
    test_database_url: str,
):
    del test_database_url
    deliveries: list[tuple[str, str, str]] = []
    push_deliveries: list[tuple[str, str, str, str]] = []
    contact_push_deliveries: list[tuple[str, str, str, str]] = []

    def fake_send_email(*, to: str, subject: str, body: str) -> None:
        deliveries.append((to, subject, body))

    def fake_send_push(session, owner_id, title, body, url="/dashboard", **kwargs):
        del session, body
        push_deliveries.append((owner_id, title, url, kwargs["category"]))
        return PushResult(success_count=1, failure_count=0)

    def fake_send_push_to_contact(session, email, title, body, url="/dashboard", **kwargs):
        del session, body
        contact_push_deliveries.append((email, title, url, kwargs["category"]))
        return PushResult(success_count=1, failure_count=0)

    monkeypatch.setattr("app.services.notification_dispatcher.send_email", fake_send_email)
    monkeypatch.setattr("app.services.notification_dispatcher.send_push_to_owner", fake_send_push)
    monkeypatch.setattr(
        "app.services.notification_dispatcher.send_push_to_contact",
        fake_send_push_to_contact,
    )

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
            log for log in logs if log.notification_type == NotificationType.OWNER_ESCALATION
        ]
        contact_alerts = [
            log
            for log in logs
            if log.notification_type == NotificationType.EMERGENCY_CONTACT_ESCALATION
        ]

        # Email + push owner alerts.
        assert len(owner_alerts) == 2
        channels = [log.channel for log in owner_alerts]
        assert "email" in channels
        assert "push" in channels
        # Contact: email + push for first contact.
        assert len(contact_alerts) == 2
        contact_channels = [log.channel for log in contact_alerts]
        assert "email" in contact_channels
        assert "push" in contact_channels
        assert deliveries[0][0] == "demo@pfoten-held.de"
        assert deliveries[1][0] == expected_first_email
        assert "/s/token-bello-public" in deliveries[0][2]
        assert "/s/token-bello-public" in deliveries[1][2]
        assert len(push_deliveries) == 1
        expected_owner_url = extract_public_check_in_url(deliveries[0][2])
        assert push_deliveries[0][2] == expected_owner_url
        assert push_deliveries[0][3] == "check_in"
        # Contact push sent to first contact email.
        assert len(contact_push_deliveries) == 1
        assert contact_push_deliveries[0][0] == expected_first_email
        assert contact_push_deliveries[0][3] == "emergency_profile"

        dispatch_notifications(session)
        logs_after_second_run = list(
            session.scalars(
                select(NotificationLog)
                .where(NotificationLog.owner_id == "owner-demo")
                .order_by(NotificationLog.created_at)
            )
        )
        assert (
            len(
                [
                    log
                    for log in logs_after_second_run
                    if log.notification_type == NotificationType.EMERGENCY_CONTACT_ESCALATION
                ]
            )
            == 2
        )

        # Advance the first contact's log past the gap so the next contact is notified.
        email_contact_log = next(log for log in contact_alerts if log.channel == "email")
        email_contact_log.created_at = datetime.now(UTC) - CONTACT_NOTIFY_GAP - timedelta(minutes=1)
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
        # 2 for first contact + 2 for second contact = 4.
        assert len(final_contact_alerts) == 4
        assert deliveries[-1][0] == expected_second_email
        assert len(contact_push_deliveries) == 2
        assert contact_push_deliveries[1][0] == expected_second_email
    finally:
        session.close()


def test_pending_dispatch_retries_failed_owner_push_until_success(
    monkeypatch,
    test_database_url: str,
):
    del test_database_url
    deliveries: list[tuple[str, str, str]] = []
    push_results = [
        PushResult(success_count=0, failure_count=1, failure_reason="delivery_failed"),
        PushResult(success_count=1, failure_count=0),
    ]
    push_calls: list[tuple[str, str, str, str]] = []

    def fake_send_email(*, to: str, subject: str, body: str) -> None:
        deliveries.append((to, subject, body))

    def fake_send_push(session, owner_id, title, body, url="/dashboard", **kwargs):
        del session
        push_calls.append((owner_id, title, url, kwargs["category"]))
        return push_results.pop(0)

    monkeypatch.setattr("app.services.notification_dispatcher.send_email", fake_send_email)
    monkeypatch.setattr("app.services.notification_dispatcher.send_push_to_owner", fake_send_push)

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
        dispatch_notifications(session)

        reminder_logs = list(
            session.scalars(
                select(NotificationLog)
                .where(
                    NotificationLog.owner_id == "owner-demo",
                    NotificationLog.notification_type == NotificationType.OWNER_REMINDER,
                )
                .order_by(NotificationLog.created_at)
            )
        )

        assert len(deliveries) == 1
        assert len(push_calls) == 2
        assert all(call[3] == "check_in" for call in push_calls)
        assert [log.status for log in reminder_logs if log.channel == "push"] == ["failed", "sent"]
    finally:
        session.close()


def test_escalation_dispatch_retries_failed_owner_push_until_success(
    monkeypatch,
    test_database_url: str,
):
    del test_database_url
    deliveries: list[tuple[str, str, str]] = []
    push_results = [
        PushResult(success_count=0, failure_count=1, failure_reason="delivery_failed"),
        PushResult(success_count=1, failure_count=0),
    ]
    push_calls: list[tuple[str, str, str, str]] = []

    def fake_send_email(*, to: str, subject: str, body: str) -> None:
        deliveries.append((to, subject, body))

    def fake_send_push(session, owner_id, title, body, url="/dashboard", **kwargs):
        del session
        push_calls.append((owner_id, title, url, kwargs["category"]))
        return push_results.pop(0)

    monkeypatch.setattr("app.services.notification_dispatcher.send_email", fake_send_email)
    monkeypatch.setattr("app.services.notification_dispatcher.send_push_to_owner", fake_send_push)
    monkeypatch.setattr(
        "app.services.notification_dispatcher.send_push_to_contact",
        lambda *a, **kw: PushResult(success_count=1, failure_count=0),
    )

    session = get_session_factory()()
    try:
        _reset_notification_flow_state(session)
        config = session.scalar(select(CheckInConfig).where(CheckInConfig.owner_id == "owner-demo"))
        assert config is not None
        config.next_scheduled_at = datetime.now(UTC) - timedelta(minutes=45)
        config.escalation_delay_minutes = 15
        session.commit()

        dispatch_notifications(session)
        dispatch_notifications(session)
        dispatch_notifications(session)

        escalation_logs = list(
            session.scalars(
                select(NotificationLog)
                .where(
                    NotificationLog.owner_id == "owner-demo",
                    NotificationLog.notification_type == NotificationType.OWNER_ESCALATION,
                )
                .order_by(NotificationLog.created_at)
            )
        )

        email_logs = [log for log in escalation_logs if log.channel == "email"]
        push_logs = [log for log in escalation_logs if log.channel == "push"]

        assert len(deliveries) >= 1
        assert len(email_logs) == 1
        assert [log.status for log in push_logs] == ["failed", "sent"]
        assert len(push_calls) == 2
        assert all(call[3] == "check_in" for call in push_calls)
    finally:
        session.close()


def test_owner_acknowledgment_stops_further_pending_push_retries(
    monkeypatch,
    test_database_url: str,
):
    del test_database_url
    push_calls: list[str] = []

    def fake_send_email(*, to: str, subject: str, body: str) -> None:
        del to, subject, body

    def fake_send_push(session, owner_id, title, body, url="/dashboard", **kwargs):
        del session, owner_id, title, body, url, kwargs
        push_calls.append("attempt")
        return PushResult(success_count=0, failure_count=1, failure_reason="delivery_failed")

    monkeypatch.setattr("app.services.notification_dispatcher.send_email", fake_send_email)
    monkeypatch.setattr("app.services.notification_dispatcher.send_push_to_owner", fake_send_push)

    session = get_session_factory()()
    try:
        _reset_notification_flow_state(session)
        config = session.scalar(select(CheckInConfig).where(CheckInConfig.owner_id == "owner-demo"))
        assert config is not None
        config.next_scheduled_at = datetime.now(UTC) - timedelta(minutes=5)
        config.escalation_delay_minutes = 30
        session.commit()

        dispatch_notifications(session)
        acknowledge_check_in(session, "owner-demo")
        session.commit()
        dispatch_notifications(session)

        assert push_calls == ["attempt"]
    finally:
        session.close()


def test_public_acknowledgment_logs_owner_notification(client, auth_headers, monkeypatch):
    deliveries: list[tuple[str, str, str]] = []

    def fake_send_email(*, to: str, subject: str, body: str) -> None:
        deliveries.append((to, subject, body))

    monkeypatch.setattr("app.services.notification_dispatcher.send_email", fake_send_email)
    monkeypatch.setattr("app.api.routes.public.send_email", fake_send_email)
    monkeypatch.setattr(
        "app.services.notification_dispatcher.send_push_to_owner", _fake_push_success
    )
    monkeypatch.setattr(
        "app.services.notification_dispatcher.send_push_to_contact",
        lambda *a, **kw: PushResult(success_count=1, failure_count=0),
    )

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


def test_pending_dispatch_respects_push_disabled(monkeypatch, test_database_url: str):
    del test_database_url
    deliveries: list[tuple[str, str, str]] = []

    def fake_send_email(*, to: str, subject: str, body: str) -> None:
        deliveries.append((to, subject, body))

    monkeypatch.setattr("app.services.notification_dispatcher.send_email", fake_send_email)
    monkeypatch.setattr(
        "app.services.notification_dispatcher.send_push_to_owner", _fake_push_success
    )

    session = get_session_factory()()
    try:
        _reset_notification_flow_state(session)
        config = session.scalar(select(CheckInConfig).where(CheckInConfig.owner_id == "owner-demo"))
        assert config is not None
        config.next_scheduled_at = datetime.now(UTC) - timedelta(minutes=5)
        config.escalation_delay_minutes = 30
        config.push_enabled = False
        config.email_enabled = True
        session.commit()

        dispatch_notifications(session)

        logs = list(
            session.scalars(
                select(NotificationLog)
                .where(NotificationLog.owner_id == "owner-demo")
                .order_by(NotificationLog.created_at)
            )
        )
        reminder_logs = [
            log for log in logs if log.notification_type == NotificationType.OWNER_REMINDER
        ]

        assert len(reminder_logs) == 1
        assert reminder_logs[0].channel == "email"
        assert len(deliveries) == 1
    finally:
        # Restore defaults for other tests.
        config = session.scalar(select(CheckInConfig).where(CheckInConfig.owner_id == "owner-demo"))
        if config:
            config.push_enabled = True
            config.email_enabled = True
            session.commit()
        session.close()


def test_pending_dispatch_respects_email_disabled(monkeypatch, test_database_url: str):
    del test_database_url
    deliveries: list[tuple[str, str, str]] = []

    def fake_send_email(*, to: str, subject: str, body: str) -> None:
        deliveries.append((to, subject, body))

    monkeypatch.setattr("app.services.notification_dispatcher.send_email", fake_send_email)
    monkeypatch.setattr(
        "app.services.notification_dispatcher.send_push_to_owner", _fake_push_success
    )

    session = get_session_factory()()
    try:
        _reset_notification_flow_state(session)
        config = session.scalar(select(CheckInConfig).where(CheckInConfig.owner_id == "owner-demo"))
        assert config is not None
        config.next_scheduled_at = datetime.now(UTC) - timedelta(minutes=5)
        config.escalation_delay_minutes = 30
        config.push_enabled = True
        config.email_enabled = False
        session.commit()

        dispatch_notifications(session)

        logs = list(
            session.scalars(
                select(NotificationLog)
                .where(NotificationLog.owner_id == "owner-demo")
                .order_by(NotificationLog.created_at)
            )
        )
        reminder_logs = [
            log for log in logs if log.notification_type == NotificationType.OWNER_REMINDER
        ]

        assert len(reminder_logs) == 1
        assert reminder_logs[0].channel == "push"
        assert len(deliveries) == 0
    finally:
        config = session.scalar(select(CheckInConfig).where(CheckInConfig.owner_id == "owner-demo"))
        if config:
            config.push_enabled = True
            config.email_enabled = True
            session.commit()
        session.close()
