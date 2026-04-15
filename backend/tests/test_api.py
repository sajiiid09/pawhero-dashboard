from fastapi import status
from uuid import uuid4

from app.db.models import NotificationLog
from app.db.session import get_session_factory


def test_healthcheck(client):
    response = client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}


def test_dashboard_summary_uses_seeded_data(client, auth_headers):
    response = client.get("/dashboard/summary", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()

    assert payload["petCount"] == 2
    assert payload["emergencyChainStatus"] == "active"
    assert payload["monitoredPet"]["name"] == "Bello"
    assert len(payload["recentCheckIns"]) == 3


def test_pets_crud_and_emergency_profile_404_after_delete(client, auth_headers):
    create_response = client.post(
        "/pets",
        headers=auth_headers,
        json={
            "name": "Milo",
            "breed": "Border Collie",
            "ageYears": 2,
            "weightKg": 15.5,
            "chipNumber": "PH-99130",
            "address": "Teststrasse 1, Berlin",
            "imageUrl": None,
            "medicalProfile": {
                "preExistingConditions": "Keine",
                "allergies": "Keine",
                "medications": "Keine",
                "vaccinationStatus": "Aktuell",
                "insurance": "Keine",
            },
            "veterinarian": {
                "name": "Praxis Mitte",
                "phone": "+49 30 1111 2222",
            },
            "feedingNotes": "Zweimal taeglich.",
            "specialNeeds": "Braucht viel Bewegung.",
            "spareKeyLocation": "Beim Concierge.",
        },
    )

    assert create_response.status_code == status.HTTP_201_CREATED
    pet_id = create_response.json()["id"]

    profile_response = client.get(f"/pets/{pet_id}/emergency-profile", headers=auth_headers)
    assert profile_response.status_code == status.HTTP_200_OK

    delete_response = client.delete(f"/pets/{pet_id}", headers=auth_headers)
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    missing_profile_response = client.get(f"/pets/{pet_id}/emergency-profile", headers=auth_headers)
    assert missing_profile_response.status_code == status.HTTP_404_NOT_FOUND


def test_emergency_contact_crud_and_reorder(client, auth_headers):
    create_response = client.post(
        "/emergency-chain/contacts",
        headers=auth_headers,
        json={
            "name": "Mara Kolb",
            "relationship": "Nachbarin",
            "phone": "+49 170 445566",
            "email": "mara@example.com",
            "priority": 2,
            "hasApartmentKey": True,
            "canTakeDog": False,
            "notes": "Kann morgens einspringen.",
        },
    )

    assert create_response.status_code == status.HTTP_201_CREATED
    created_contact = create_response.json()

    chain_response = client.get("/emergency-chain", headers=auth_headers)
    assert chain_response.status_code == status.HTTP_200_OK
    priorities = [item["priority"] for item in chain_response.json()]
    assert priorities == [1, 2, 3]

    move_response = client.post(
        f"/emergency-chain/contacts/{created_contact['id']}/move",
        headers=auth_headers,
        json={"direction": "up"},
    )
    assert move_response.status_code == status.HTTP_200_OK
    assert move_response.json()[1]["id"] == created_contact["id"]

    delete_response = client.delete(
        f"/emergency-chain/contacts/{created_contact['id']}",
        headers=auth_headers,
    )
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    after_delete_response = client.get("/emergency-chain", headers=auth_headers)
    assert [item["priority"] for item in after_delete_response.json()] == [1, 2]


def test_check_in_config_updates_next_scheduled_at(client, auth_headers):
    get_response = client.get("/check-in-config", headers=auth_headers)
    assert get_response.status_code == status.HTTP_200_OK

    update_response = client.put(
        "/check-in-config",
        headers=auth_headers,
        json={
            "intervalHours": 8,
            "escalationDelayMinutes": 15,
            "primaryMethod": "push",
            "backupMethod": "email",
        },
    )

    assert update_response.status_code == status.HTTP_200_OK
    payload = update_response.json()
    assert payload["intervalHours"] == 8
    assert payload["escalationDelayMinutes"] == 15
    assert payload["nextScheduledAt"]


def test_auth_register_and_login(client):
    register_response = client.post(
        "/auth/register",
        json={
            "email": "new-user@example.com",
            "password": "secure123",
            "display_name": "Test User",
        },
    )
    assert register_response.status_code == status.HTTP_201_CREATED
    register_data = register_response.json()
    assert "access_token" in register_data
    assert register_data["display_name"] == "Test User"

    login_response = client.post(
        "/auth/login",
        json={
            "email": "new-user@example.com",
            "password": "secure123",
        },
    )
    assert login_response.status_code == status.HTTP_200_OK
    login_data = login_response.json()
    assert "access_token" in login_data

    wrong_password_response = client.post(
        "/auth/login",
        json={
            "email": "new-user@example.com",
            "password": "wrong",
        },
    )
    assert wrong_password_response.status_code == status.HTTP_401_UNAUTHORIZED

    duplicate_response = client.post(
        "/auth/register",
        json={
            "email": "new-user@example.com",
            "password": "another123",
            "display_name": "Duplicate",
        },
    )
    assert duplicate_response.status_code == status.HTTP_409_CONFLICT


def test_unauthenticated_requests_return_401(client):
    response = client.get("/dashboard/summary")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_public_emergency_profile(client):
    response = client.get("/public/emergency-profile/token-bello-public")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["pet"]["name"] == "Bello"

    not_found_response = client.get("/public/emergency-profile/nonexistent-token")
    assert not_found_response.status_code == status.HTTP_404_NOT_FOUND


def test_emergency_access_token_endpoint(client, auth_headers):
    response = client.get("/pets/pet-bello/emergency-access-token", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["access_token"] == "token-bello-public"

    regenerate_response = client.post(
        "/pets/pet-bello/emergency-access-token/regenerate",
        headers=auth_headers,
    )
    assert regenerate_response.status_code == status.HTTP_200_OK
    new_data = regenerate_response.json()
    assert new_data["access_token"] != "token-bello-public"


def test_check_in_acknowledge_creates_event(client, auth_headers):
    response = client.post("/check-in/acknowledge", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["mode"] == "normal"
    assert data["nextCheckInAt"]


def test_check_in_status_returns_normal(client, auth_headers):
    response = client.get("/check-in/status", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["mode"] == "normal"


def test_check_in_events_returns_history(client, auth_headers):
    # First acknowledge to create an event.
    client.post("/check-in/acknowledge", headers=auth_headers)

    response = client.get("/check-in/events", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    events = response.json()
    assert len(events) >= 1
    assert events[0]["status"] == "acknowledged"
    assert events[0]["method"] == "webapp"


def test_escalation_history_empty_initially(client, auth_headers):
    response = client.get("/check-in/escalation-history", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_dashboard_escalation_status_is_dynamic(client, auth_headers):
    response = client.get("/dashboard/summary", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    escalation = response.json()["escalationStatus"]
    assert escalation["mode"] == "normal"
    assert escalation["title"] == "Normalbetrieb"


def test_notifications_response_uses_camel_case(client, auth_headers):
    log_id = f"notif-{uuid4().hex[:8]}"
    session = get_session_factory()()

    try:
        session.add(
            NotificationLog(
                id=log_id,
                owner_id="owner-demo",
                escalation_event_id=None,
                recipient_email="demo+notif@pfoten-held.de",
                notification_type="reminder",
                status="sent",
                error_message=None,
            )
        )
        session.commit()
    finally:
        session.close()

    response = client.get("/notifications", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    item = next((entry for entry in payload if entry["id"] == log_id), None)

    assert item is not None
    assert item["recipientEmail"] == "demo+notif@pfoten-held.de"
    assert item["notificationType"] == "reminder"
    assert item["errorMessage"] is None
    assert item["createdAt"]
    assert "recipient_email" not in item
    assert "notification_type" not in item
    assert "error_message" not in item
    assert "created_at" not in item
