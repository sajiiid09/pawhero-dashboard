"""Tests for push subscription CRUD and VAPID endpoint."""

from __future__ import annotations

from unittest.mock import patch

from fastapi import status

from app.db.models import CheckInConfig, NotificationLog, NotificationType, PushSubscription
from app.db.session import get_session_factory
from app.services.push import PushResult
from sqlalchemy import select


def test_vapid_public_key_endpoint(client):
    response = client.get("/push/vapid-public-key")
    assert response.status_code == status.HTTP_200_OK
    assert "publicKey" in response.json()


def test_push_subscription_create_and_list(client, auth_headers):
    save_response = client.post(
        "/push/subscriptions",
        headers=auth_headers,
        json={
            "endpoint": "https://push.example.com/sub/123",
            "p256dh": "test-p256dh-key",
            "auth": "test-auth-key",
            "userAgent": "TestBrowser/1.0",
        },
    )
    assert save_response.status_code == status.HTTP_200_OK
    data = save_response.json()
    assert data["endpoint"] == "https://push.example.com/sub/123"

    list_response = client.get("/push/subscriptions", headers=auth_headers)
    assert list_response.status_code == status.HTTP_200_OK
    subs = list_response.json()
    assert len(subs) >= 1
    assert subs[0]["endpoint"] == "https://push.example.com/sub/123"


def test_push_subscription_idempotent_by_endpoint(client, auth_headers):
    payload = {
        "endpoint": "https://push.example.com/sub/idem",
        "p256dh": "key1",
        "auth": "auth1",
    }

    first = client.post("/push/subscriptions", headers=auth_headers, json=payload)
    assert first.status_code == status.HTTP_200_OK

    payload["p256dh"] = "key2"
    second = client.post("/push/subscriptions", headers=auth_headers, json=payload)
    assert second.status_code == status.HTTP_200_OK

    list_response = client.get("/push/subscriptions", headers=auth_headers)
    subs = list_response.json()
    matching = [s for s in subs if s["endpoint"] == "https://push.example.com/sub/idem"]
    assert len(matching) == 1


def test_push_subscription_revoke(client, auth_headers):
    save_response = client.post(
        "/push/subscriptions",
        headers=auth_headers,
        json={
            "endpoint": "https://push.example.com/sub/revoke-me",
            "p256dh": "revoke-key",
            "auth": "revoke-auth",
        },
    )
    assert save_response.status_code == status.HTTP_200_OK

    revoke_response = client.request(
        "DELETE",
        "/push/subscriptions",
        headers=auth_headers,
        json={
            "endpoint": "https://push.example.com/sub/revoke-me",
            "p256dh": "revoke-key",
            "auth": "revoke-auth",
        },
    )
    assert revoke_response.status_code == status.HTTP_204_NO_CONTENT


def test_push_subscription_revoke_not_found(client, auth_headers):
    revoke_response = client.request(
        "DELETE",
        "/push/subscriptions",
        headers=auth_headers,
        json={
            "endpoint": "https://push.example.com/sub/nonexistent",
            "p256dh": "x",
            "auth": "y",
        },
    )
    assert revoke_response.status_code == status.HTTP_404_NOT_FOUND


def test_test_push_endpoint_returns_result(client, auth_headers, monkeypatch):
    def fake_send(*args, **kwargs):
        return PushResult(success_count=1, failure_count=0)

    monkeypatch.setattr("app.services.push.send_push_to_owner", fake_send)

    response = client.post("/push/test", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["successCount"] == 1
    assert data["failureCount"] == 0


def test_dispatcher_real_push_called_when_enabled(monkeypatch, test_database_url: str):
    del test_database_url
    push_calls: list[tuple[str, str, str]] = []

    def fake_send_push(session, owner_id, title, body, url="/dashboard"):
        push_calls.append((owner_id, title, url))
        return PushResult(success_count=1, failure_count=0)

    def fake_send_email(**kwargs):
        pass

    monkeypatch.setattr("app.services.notification_dispatcher.send_push_to_owner", fake_send_push)
    monkeypatch.setattr("app.services.notification_dispatcher.send_email", fake_send_email)

    session = get_session_factory()()
    try:
        session.query(NotificationLog).filter(NotificationLog.owner_id == "owner-demo").delete()
        session.query(PushSubscription).filter(PushSubscription.owner_id == "owner-demo").delete()
        session.commit()

        config = session.scalar(select(CheckInConfig).where(CheckInConfig.owner_id == "owner-demo"))
        assert config is not None
        config.next_scheduled_at = __import__("datetime").datetime.now(
            __import__("datetime").UTC
        ) - __import__("datetime").timedelta(minutes=5)
        config.escalation_delay_minutes = 30
        config.push_enabled = True
        config.email_enabled = True
        session.commit()

        from app.services.notification_dispatcher import dispatch_notifications

        dispatch_notifications(session)

        assert len(push_calls) == 1
        assert push_calls[0][1] == "Check-In erforderlich"
    finally:
        config = session.scalar(select(CheckInConfig).where(CheckInConfig.owner_id == "owner-demo"))
        if config:
            config.push_enabled = True
            config.email_enabled = True
            session.commit()
        session.close()


def test_push_subscriptions_require_auth(client):
    response = client.get("/push/subscriptions")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    save_response = client.post(
        "/push/subscriptions",
        json={"endpoint": "https://x.com", "p256dh": "k", "auth": "a"},
    )
    assert save_response.status_code == status.HTTP_401_UNAUTHORIZED
