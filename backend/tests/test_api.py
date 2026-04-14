from fastapi import status


def test_healthcheck(client):
    response = client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}


def test_dashboard_summary_uses_seeded_data(client):
    response = client.get("/dashboard/summary")

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()

    assert payload["petCount"] == 2
    assert payload["emergencyChainStatus"] == "active"
    assert payload["monitoredPet"]["name"] == "Bello"
    assert len(payload["recentCheckIns"]) == 3


def test_pets_crud_and_emergency_profile_404_after_delete(client):
    create_response = client.post(
        "/pets",
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

    profile_response = client.get(f"/pets/{pet_id}/emergency-profile")
    assert profile_response.status_code == status.HTTP_200_OK

    delete_response = client.delete(f"/pets/{pet_id}")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    missing_profile_response = client.get(f"/pets/{pet_id}/emergency-profile")
    assert missing_profile_response.status_code == status.HTTP_404_NOT_FOUND


def test_emergency_contact_crud_and_reorder(client):
    create_response = client.post(
        "/emergency-chain/contacts",
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

    chain_response = client.get("/emergency-chain")
    assert chain_response.status_code == status.HTTP_200_OK
    priorities = [item["priority"] for item in chain_response.json()]
    assert priorities == [1, 2, 3]

    move_response = client.post(
        f"/emergency-chain/contacts/{created_contact['id']}/move",
        json={"direction": "up"},
    )
    assert move_response.status_code == status.HTTP_200_OK
    assert move_response.json()[1]["id"] == created_contact["id"]

    delete_response = client.delete(f"/emergency-chain/contacts/{created_contact['id']}")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    after_delete_response = client.get("/emergency-chain")
    assert [item["priority"] for item in after_delete_response.json()] == [1, 2]


def test_check_in_config_updates_next_scheduled_at(client):
    get_response = client.get("/check-in-config")
    assert get_response.status_code == status.HTTP_200_OK

    update_response = client.put(
        "/check-in-config",
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
