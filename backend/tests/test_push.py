"""Tests for push subscription CRUD and VAPID endpoint."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

from fastapi import status
from pywebpush import WebPushException
from sqlalchemy import select

from app.db.models import (
    CheckInConfig,
    ContactPushSubscription,
    EmergencyChainEntry,
    EmergencyContact,
    NotificationLog,
    Owner,
    Pet,
    PushSubscription,
)
from app.db.session import get_session_factory
from app.services.auth import create_access_token, hash_password
from app.services.push import PushResult


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


def test_push_subscription_transfers_endpoint_to_new_owner(client):
    owner_a_id = _create_owner()
    owner_b_id = _create_owner()
    owner_a_headers = _auth_headers(owner_a_id)
    owner_b_headers = _auth_headers(owner_b_id)
    payload = {
        "endpoint": "https://push.example.com/sub/shared-device",
        "p256dh": "key-owner-a",
        "auth": "auth-owner-a",
        "userAgent": "SharedBrowser/1.0",
    }

    first_response = client.post("/push/subscriptions", headers=owner_a_headers, json=payload)
    assert first_response.status_code == status.HTTP_200_OK

    second_response = client.post(
        "/push/subscriptions",
        headers=owner_b_headers,
        json={**payload, "p256dh": "key-owner-b", "auth": "auth-owner-b"},
    )
    assert second_response.status_code == status.HTTP_200_OK
    assert second_response.json()["id"] == first_response.json()["id"]

    owner_a_subs = client.get("/push/subscriptions", headers=owner_a_headers)
    owner_b_subs = client.get("/push/subscriptions", headers=owner_b_headers)
    assert owner_a_subs.status_code == status.HTTP_200_OK
    assert owner_a_subs.json() == []
    assert owner_b_subs.status_code == status.HTTP_200_OK
    assert [sub["endpoint"] for sub in owner_b_subs.json()] == [payload["endpoint"]]

    session = get_session_factory()()
    try:
        subscription = session.scalar(
            select(PushSubscription).where(PushSubscription.endpoint == payload["endpoint"])
        )
        assert subscription is not None
        assert subscription.owner_id == owner_b_id
        assert subscription.revoked_at is None
        assert subscription.p256dh == "key-owner-b"
        assert subscription.auth == "auth-owner-b"
    finally:
        session.close()


def test_push_subscription_reactivates_revoked_endpoint_for_current_owner(client):
    owner_a_id = _create_owner()
    owner_b_id = _create_owner()
    owner_a_headers = _auth_headers(owner_a_id)
    owner_b_headers = _auth_headers(owner_b_id)
    payload = {
        "endpoint": "https://push.example.com/sub/revive-me",
        "p256dh": "revive-key-a",
        "auth": "revive-auth-a",
    }

    save_response = client.post("/push/subscriptions", headers=owner_a_headers, json=payload)
    assert save_response.status_code == status.HTTP_200_OK

    revoke_response = client.request(
        "DELETE",
        "/push/subscriptions",
        headers=owner_a_headers,
        json=payload,
    )
    assert revoke_response.status_code == status.HTTP_204_NO_CONTENT

    restore_response = client.post(
        "/push/subscriptions",
        headers=owner_b_headers,
        json={**payload, "p256dh": "revive-key-b", "auth": "revive-auth-b"},
    )
    assert restore_response.status_code == status.HTTP_200_OK

    owner_a_subs = client.get("/push/subscriptions", headers=owner_a_headers)
    owner_b_subs = client.get("/push/subscriptions", headers=owner_b_headers)
    assert owner_a_subs.status_code == status.HTTP_200_OK
    assert owner_a_subs.json() == []
    assert owner_b_subs.status_code == status.HTTP_200_OK
    assert [sub["endpoint"] for sub in owner_b_subs.json()] == [payload["endpoint"]]

    session = get_session_factory()()
    try:
        subscription = session.scalar(
            select(PushSubscription).where(PushSubscription.endpoint == payload["endpoint"])
        )
        assert subscription is not None
        assert subscription.owner_id == owner_b_id
        assert subscription.revoked_at is None
        assert subscription.p256dh == "revive-key-b"
        assert subscription.auth == "revive-auth-b"
    finally:
        session.close()


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


def test_push_preview_endpoint_returns_result(client, auth_headers, monkeypatch):
    captured: dict[str, str] = {}

    def fake_send(*args, **kwargs):
        captured["url"] = kwargs["url"]
        captured["category"] = kwargs["category"]
        return PushResult(success_count=1, failure_count=0)

    monkeypatch.setattr("app.services.push.send_push_to_owner", fake_send)

    response = client.post("/push/preview", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["successCount"] == 1
    assert data["failureCount"] == 0
    assert "/c/" in captured["url"]
    assert "/check-in" not in captured["url"]
    assert captured["category"] == "check_in"


def test_push_preview_persists_revoked_dead_endpoint(client, monkeypatch):
    owner_id = _create_owner()
    owner_headers = _auth_headers(owner_id)
    payload = {
        "endpoint": "https://push.example.com/sub/dead-endpoint",
        "p256dh": "dead-key",
        "auth": "dead-auth",
    }
    save_response = client.post("/push/subscriptions", headers=owner_headers, json=payload)
    assert save_response.status_code == status.HTTP_200_OK

    webpush_calls = 0

    def fake_webpush(*args, **kwargs):
        del args, kwargs
        nonlocal webpush_calls
        webpush_calls += 1
        raise WebPushException("gone", response=SimpleNamespace(status_code=410))

    monkeypatch.setattr(
        "app.services.push.get_settings",
        lambda: SimpleNamespace(
            vapid_private_key="test-private-key",
            vapid_public_key="test-public-key",
            vapid_subject="mailto:test@example.com",
            app_url="https://app.bdtextilehub.com",
        ),
    )
    monkeypatch.setattr("app.services.push.webpush", fake_webpush)

    response = client.post("/push/preview", headers=owner_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"successCount": 0, "failureCount": 1}

    session = get_session_factory()()
    try:
        subscription = session.scalar(
            select(PushSubscription).where(PushSubscription.endpoint == payload["endpoint"])
        )
        assert subscription is not None
        assert subscription.revoked_at is not None
    finally:
        session.close()

    second_response = client.post("/push/preview", headers=owner_headers)
    assert second_response.status_code == status.HTTP_200_OK
    assert second_response.json() == {"successCount": 0, "failureCount": 1}
    assert webpush_calls == 1


def test_send_push_to_owner_uses_subscription_info(monkeypatch):
    owner_id = _create_owner()
    captured_kwargs: dict[str, object] = {}

    session = get_session_factory()()
    try:
        session.add(
            PushSubscription(
                id=f"sub-{uuid4().hex[:8]}",
                owner_id=owner_id,
                endpoint="https://push.example.com/sub/owner-shape",
                p256dh="owner-p256dh",
                auth="owner-auth",
                user_agent="TestBrowser/1.0",
                last_seen_at=datetime.now(UTC),
            )
        )
        session.commit()

        def fake_webpush(*args, **kwargs):
            del args
            captured_kwargs.update(kwargs)

        monkeypatch.setattr(
            "app.services.push.get_settings",
            lambda: SimpleNamespace(
                vapid_private_key="test-private-key",
                vapid_public_key="test-public-key",
                vapid_subject="mailto:test@example.com",
            ),
        )
        monkeypatch.setattr("app.services.push.webpush", fake_webpush)

        from app.services.push import send_push_to_owner

        result = send_push_to_owner(
            session,
            owner_id,
            title="Check-In erforderlich",
            body="Bitte bestaetige jetzt.",
            url="https://app.bdtextilehub.com/c/test-token",
            category="check_in",
        )

        assert result.success_count == 1
        assert result.failure_count == 0
        assert "subscription_info" in captured_kwargs
        assert "subscription" not in captured_kwargs
        assert captured_kwargs["subscription_info"] == {
            "endpoint": "https://push.example.com/sub/owner-shape",
            "keys": {"p256dh": "owner-p256dh", "auth": "owner-auth"},
        }
    finally:
        session.close()


def test_send_push_to_owner_classifies_backend_integration_error(monkeypatch):
    owner_id = _create_owner()

    session = get_session_factory()()
    try:
        session.add(
            PushSubscription(
                id=f"sub-{uuid4().hex[:8]}",
                owner_id=owner_id,
                endpoint="https://push.example.com/sub/integration-error",
                p256dh="owner-p256dh",
                auth="owner-auth",
                user_agent="TestBrowser/1.0",
                last_seen_at=datetime.now(UTC),
            )
        )
        session.commit()

        monkeypatch.setattr(
            "app.services.push.get_settings",
            lambda: SimpleNamespace(
                vapid_private_key="test-private-key",
                vapid_public_key="test-public-key",
                vapid_subject="mailto:test@example.com",
            ),
        )
        monkeypatch.setattr(
            "app.services.push.webpush",
            lambda *args, **kwargs: (_ for _ in ()).throw(TypeError("wrong keyword")),
        )

        from app.services.push import send_push_to_owner

        result = send_push_to_owner(
            session,
            owner_id,
            title="Check-In erforderlich",
            body="Bitte bestaetige jetzt.",
            url="https://app.bdtextilehub.com/c/test-token",
            category="check_in",
        )

        assert result.success_count == 0
        assert result.failure_count == 1
        assert result.failure_reason == "integration_error"
    finally:
        session.close()


def test_push_diagnostics_include_last_failure_reason(client, auth_headers, monkeypatch):
    def fake_send(*args, **kwargs):
        del args, kwargs
        return PushResult(
            success_count=0,
            failure_count=1,
            failure_reason="no_active_subscriptions",
        )

    monkeypatch.setattr("app.services.notification_dispatcher.send_push_to_owner", fake_send)
    monkeypatch.setattr("app.services.notification_dispatcher.send_email", lambda **kwargs: None)

    session = get_session_factory()()
    try:
        session.query(NotificationLog).filter(NotificationLog.owner_id == "owner-demo").delete()
        config = session.scalar(select(CheckInConfig).where(CheckInConfig.owner_id == "owner-demo"))
        assert config is not None
        config.next_scheduled_at = datetime.now(UTC) - timedelta(minutes=5)
        config.escalation_delay_minutes = 30
        session.commit()

        from app.services.notification_dispatcher import dispatch_notifications

        dispatch_notifications(session)
    finally:
        session.close()

    response = client.get("/push/diagnostics", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["lastFailureReason"] == (
        "Push-Zustellung fehlgeschlagen: Keine aktiven Push-Abonnements fuer diesen Account."
    )
    assert payload["lastFailureAt"] is not None


def test_push_diagnostics_include_backend_integration_failure_reason(
    client,
    auth_headers,
    monkeypatch,
):
    def fake_send(*args, **kwargs):
        del args, kwargs
        return PushResult(success_count=0, failure_count=1, failure_reason="integration_error")

    monkeypatch.setattr("app.services.notification_dispatcher.send_push_to_owner", fake_send)
    monkeypatch.setattr("app.services.notification_dispatcher.send_email", lambda **kwargs: None)

    session = get_session_factory()()
    try:
        session.query(NotificationLog).filter(NotificationLog.owner_id == "owner-demo").delete()
        config = session.scalar(select(CheckInConfig).where(CheckInConfig.owner_id == "owner-demo"))
        assert config is not None
        config.next_scheduled_at = datetime.now(UTC) - timedelta(minutes=5)
        config.escalation_delay_minutes = 30
        session.commit()

        from app.services.notification_dispatcher import dispatch_notifications

        dispatch_notifications(session)
    finally:
        session.close()

    response = client.get("/push/diagnostics", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["lastFailureReason"] == (
        "Push-Zustellung nicht moeglich: Interner Web-Push-Fehler im Backend. Deployment und "
        "Abhaengigkeiten pruefen."
    )
    assert payload["lastFailureAt"] is not None


def test_contact_push_subscription_requires_matching_public_contact_email(client):
    response = client.post(
        "/public/emergency-profile/token-bello-public/contact-push",
        json={
            "email": "intruder@example.com",
            "endpoint": "https://push.example.com/sub/contact-invalid",
            "p256dh": "test-p256dh-key",
            "auth": "test-auth-key",
            "userAgent": "TestBrowser/1.0",
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Kontaktperson" in response.json()["detail"]


def test_contact_push_subscription_status_and_revoke_are_token_scoped(client):
    profile_response = client.get("/public/emergency-profile/token-bello-public")
    assert profile_response.status_code == status.HTTP_200_OK
    contact_email = profile_response.json()["contacts"][0]["email"]
    endpoint = "https://push.example.com/sub/contact-valid"

    subscribe_response = client.post(
        "/public/emergency-profile/token-bello-public/contact-push",
        json={
            "email": contact_email,
            "endpoint": endpoint,
            "p256dh": "test-p256dh-key",
            "auth": "test-auth-key",
            "userAgent": "TestBrowser/1.0",
        },
    )
    assert subscribe_response.status_code == status.HTTP_200_OK
    assert subscribe_response.json() == {"success": True}

    status_response = client.get(
        f"/public/emergency-profile/token-bello-public/contact-push?email={contact_email}"
    )
    assert status_response.status_code == status.HTTP_200_OK
    assert status_response.json() == {
        "email": contact_email.lower(),
        "endpoints": [endpoint],
    }

    wrong_email_revoke = client.request(
        "DELETE",
        "/public/emergency-profile/token-bello-public/contact-push",
        json={"email": "wrong@example.com", "endpoint": endpoint},
    )
    assert wrong_email_revoke.status_code == status.HTTP_403_FORBIDDEN

    revoke_response = client.request(
        "DELETE",
        "/public/emergency-profile/token-bello-public/contact-push",
        json={"email": contact_email, "endpoint": endpoint},
    )
    assert revoke_response.status_code == status.HTTP_200_OK
    assert revoke_response.json() == {"success": True}

    session = get_session_factory()()
    try:
        subscription = session.scalar(
            select(ContactPushSubscription).where(ContactPushSubscription.endpoint == endpoint)
        )
        assert subscription is not None
        assert subscription.email == contact_email.lower()
        assert subscription.revoked_at is not None
    finally:
        session.close()


def test_contact_push_email_global_delivery_allows_other_owner_dispatch(
    client,
    monkeypatch,
    test_database_url: str,
):
    del test_database_url
    profile_response = client.get("/public/emergency-profile/token-bello-public")
    assert profile_response.status_code == status.HTTP_200_OK
    shared_contact_email = profile_response.json()["contacts"][0]["email"]
    endpoint = "https://push.example.com/sub/contact-shared"

    subscribe_response = client.post(
        "/public/emergency-profile/token-bello-public/contact-push",
        json={
            "email": shared_contact_email,
            "endpoint": endpoint,
            "p256dh": "shared-p256dh-key",
            "auth": "shared-auth-key",
            "userAgent": "SharedBrowser/1.0",
        },
    )
    assert subscribe_response.status_code == status.HTTP_200_OK

    webpush_calls: list[str] = []

    def fake_webpush(*args, **kwargs):
        webpush_calls.append(kwargs["subscription_info"]["endpoint"])

    monkeypatch.setattr(
        "app.services.contact_push.get_settings",
        lambda: SimpleNamespace(
            vapid_private_key="test-private-key",
            vapid_public_key="test-public-key",
            vapid_subject="mailto:test@example.com",
        ),
    )
    monkeypatch.setattr("app.services.contact_push.webpush", fake_webpush)
    monkeypatch.setattr(
        "app.services.notification_dispatcher.send_push_to_owner",
        lambda *a, **kw: PushResult(success_count=1, failure_count=0),
    )
    monkeypatch.setattr("app.services.notification_dispatcher.send_email", lambda **kwargs: None)

    second_owner_id = _create_owner()
    _add_pet_and_contact(
        owner_id=second_owner_id,
        access_token="token-second-owner-public",
        contact_email=shared_contact_email,
    )

    session = get_session_factory()()
    try:
        config = session.scalar(
            select(CheckInConfig).where(CheckInConfig.owner_id == second_owner_id)
        )
        assert config is not None
        config.next_scheduled_at = datetime.now(UTC) - timedelta(minutes=45)
        config.escalation_delay_minutes = 15
        session.commit()

        from app.services.notification_dispatcher import dispatch_notifications

        dispatch_notifications(session)

        assert webpush_calls == [endpoint]
    finally:
        session.close()


def test_send_push_to_contact_uses_subscription_info(client, monkeypatch):
    profile_response = client.get("/public/emergency-profile/token-bello-public")
    assert profile_response.status_code == status.HTTP_200_OK
    contact_email = profile_response.json()["contacts"][0]["email"]
    endpoint = "https://push.example.com/sub/contact-shape"

    session = get_session_factory()()
    try:
        session.query(ContactPushSubscription).filter(
            ContactPushSubscription.email == contact_email.lower()
        ).delete()
        session.commit()
    finally:
        session.close()

    subscribe_response = client.post(
        "/public/emergency-profile/token-bello-public/contact-push",
        json={
            "email": contact_email,
            "endpoint": endpoint,
            "p256dh": "contact-p256dh",
            "auth": "contact-auth",
            "userAgent": "SharedBrowser/1.0",
        },
    )
    assert subscribe_response.status_code == status.HTTP_200_OK

    captured_kwargs: dict[str, object] = {}

    def fake_webpush(*args, **kwargs):
        del args
        captured_kwargs.update(kwargs)

    monkeypatch.setattr(
        "app.services.contact_push.get_settings",
        lambda: SimpleNamespace(
            vapid_private_key="test-private-key",
            vapid_public_key="test-public-key",
            vapid_subject="mailto:test@example.com",
        ),
    )
    monkeypatch.setattr("app.services.contact_push.webpush", fake_webpush)

    from app.services.contact_push import send_push_to_contact

    session = get_session_factory()()
    try:
        result = send_push_to_contact(
            session,
            contact_email,
            title="Notfallprofil",
            body="Bitte oeffne das Profil.",
            url="https://app.bdtextilehub.com/s/test-token",
        )

        assert result.success_count == 1
        assert result.failure_count == 0
        assert "subscription_info" in captured_kwargs
        assert "subscription" not in captured_kwargs
        assert captured_kwargs["subscription_info"] == {
            "endpoint": endpoint,
            "keys": {"p256dh": "contact-p256dh", "auth": "contact-auth"},
        }
    finally:
        session.close()


def test_dispatcher_real_push_called_when_enabled(monkeypatch, test_database_url: str):
    del test_database_url
    push_calls: list[tuple[str, str, str]] = []

    def fake_send_push(session, owner_id, title, body, url="/dashboard", **kwargs):
        del kwargs
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


def _create_owner() -> str:
    owner_id = f"owner-{uuid4().hex[:8]}"
    session = get_session_factory()()

    try:
        session.add(
            Owner(
                id=owner_id,
                email=f"{owner_id}@example.com",
                display_name=f"Owner {owner_id}",
                password_hash=hash_password("secure123"),
                email_verified=True,
            )
        )
        session.add(
            CheckInConfig(
                owner_id=owner_id,
                interval_hours=12,
                escalation_delay_minutes=30,
                push_enabled=True,
                email_enabled=True,
                next_scheduled_at=datetime.now(UTC) + timedelta(minutes=30),
            )
        )
        session.commit()
    finally:
        session.close()

    return owner_id


def _auth_headers(owner_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(owner_id)}"}


def _add_pet_and_contact(owner_id: str, access_token: str, contact_email: str) -> None:
    session = get_session_factory()()
    try:
        pet_id = f"pet-{uuid4().hex[:8]}"
        contact_id = f"contact-{uuid4().hex[:8]}"
        session.add(
            Pet(
                id=pet_id,
                owner_id=owner_id,
                name="Milo",
                breed="Mischling",
                age_years=4,
                weight_kg=18.0,
                chip_number=f"chip-{uuid4().hex[:8]}",
                address="Teststrasse 1, Berlin",
                pre_existing_conditions="Keine",
                allergies="Keine",
                medications="Keine",
                vaccination_status="Aktuell",
                insurance="Vorhanden",
                veterinarian_name="Dr. Test",
                veterinarian_phone="+49 30 123456",
                feeding_notes="2x taeglich",
                special_needs="Keine",
                spare_key_location="Beim Nachbarn",
                emergency_access_token=access_token,
            )
        )
        session.add(
            EmergencyContact(
                id=contact_id,
                owner_id=owner_id,
                name="Shared Contact",
                relationship_label="Freund",
                phone="+49 170 0000000",
                email=contact_email,
                has_apartment_key=True,
                can_take_dog=True,
                notes="Kann helfen",
            )
        )
        session.add(
            EmergencyChainEntry(
                id=f"entry-{contact_id}",
                owner_id=owner_id,
                contact_id=contact_id,
                priority=1,
            )
        )
        session.commit()
    finally:
        session.close()
