from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.config import get_settings
from app.db.models import (
    CheckInConfig,
    CheckInEvent,
    EmergencyChainEntry,
    EmergencyContact,
    Owner,
    Pet,
)
from app.db.session import get_session_factory
from app.services.auth import hash_password


def seed_demo_data() -> None:
    settings = get_settings()
    session = get_session_factory()()

    try:
        owner = session.scalar(select(Owner).where(Owner.id == settings.demo_owner_id))
        if owner is not None:
            return

        owner = Owner(
            id=settings.demo_owner_id,
            email="demo@pfoten-held.de",
            display_name="Pfoten-Held Demo",
            password_hash=hash_password("demo1234"),
            email_verified=True,
        )
        session.add(owner)

        now = datetime.now(UTC)

        session.add_all(
            [
                Pet(
                    id="pet-bello",
                    owner_id=owner.id,
                    emergency_access_token="token-bello-public",
                    name="Bello",
                    breed="Schaeferhund",
                    age_years=5,
                    weight_kg=32,
                    chip_number="PH-99128",
                    address="Bergmannstrasse 18, 10961 Berlin",
                    image_url=None,
                    pre_existing_conditions="Keine aktiven Vorerkrankungen",
                    allergies="Keine bekannten Allergien",
                    medications="Keine taeglichen Medikamente",
                    vaccination_status="Impfschutz aktuell",
                    insurance="Uelzener Tierkrankenversicherung",
                    veterinarian_name="Dr. Hans Mueller",
                    veterinarian_phone="+49 30 8899 2200",
                    feeding_notes="Morgens Trockenfutter, abends Nassfutter. Leckerlis beruhigen bei Stress.",
                    special_needs="Sehr nervoes bei lauten Geraeuschen. Ruhig ansprechen und langsam naehern.",
                    spare_key_location="Ersatzschluessel im Schluesseltresor im Kellerabteil.",
                    created_at=now - timedelta(hours=1),
                ),
                Pet(
                    id="pet-luna",
                    owner_id=owner.id,
                    emergency_access_token="token-luna-public",
                    name="Luna",
                    breed="Mischling",
                    age_years=3,
                    weight_kg=18,
                    chip_number="PH-99129",
                    address="Bergmannstrasse 18, 10961 Berlin",
                    image_url=None,
                    pre_existing_conditions="Leichte Futtermittelunvertraeglichkeit",
                    allergies="Huehnerprotein vermeiden",
                    medications="Bei Bedarf Magenpaste im Vorratsschrank",
                    vaccination_status="Naechste Auffrischung im Oktober",
                    insurance="Keine Versicherung hinterlegt",
                    veterinarian_name="Tierarztpraxis Kreuzberg",
                    veterinarian_phone="+49 30 4455 7700",
                    feeding_notes="Nur sensitiv Futter aus der linken Kuechenschublade.",
                    special_needs="Braucht vor dem Schlafen eine kurze Runde.",
                    spare_key_location="Schluessel bei Nachbarin in Wohnung 4B hinterlegt.",
                    created_at=now - timedelta(hours=2),
                ),
            ]
        )

        session.add_all(
            [
                EmergencyContact(
                    id="contact-beate",
                    owner_id=owner.id,
                    name="Beate Zimmer",
                    relationship_label="Partnerin",
                    phone="+49 170 112233",
                    email="beate@pfoten-held.de",
                    has_apartment_key=True,
                    can_take_dog=True,
                    notes="Kennt beide Hunde und kann sofort vorbeikommen.",
                    created_at=now - timedelta(hours=1),
                ),
                EmergencyContact(
                    id="contact-hans",
                    owner_id=owner.id,
                    name="Dr. Hans Mueller",
                    relationship_label="Tierarzt",
                    phone="+49 30 8899 2200",
                    email="praxis@mueller-tierarzt.de",
                    has_apartment_key=False,
                    can_take_dog=False,
                    notes="Bitte zuerst anrufen. Praxis hat Notfalldienst bis 22 Uhr.",
                    created_at=now - timedelta(hours=2),
                ),
            ]
        )

        session.add_all(
            [
                EmergencyChainEntry(
                    id="entry-beate",
                    owner_id=owner.id,
                    contact_id="contact-beate",
                    priority=1,
                ),
                EmergencyChainEntry(
                    id="entry-hans",
                    owner_id=owner.id,
                    contact_id="contact-hans",
                    priority=2,
                ),
            ]
        )

        session.add(
            CheckInConfig(
                owner_id=owner.id,
                interval_hours=12,
                escalation_delay_minutes=30,
                push_enabled=True,
                email_enabled=True,
                next_scheduled_at=now + timedelta(minutes=42),
            )
        )

        session.add_all(
            [
                CheckInEvent(
                    id="ci-1",
                    owner_id=owner.id,
                    status="acknowledged",
                    acknowledged_at=now - timedelta(hours=4),
                    method="push",
                    created_at=now - timedelta(hours=4),
                ),
                CheckInEvent(
                    id="ci-2",
                    owner_id=owner.id,
                    status="acknowledged",
                    acknowledged_at=now - timedelta(hours=16),
                    method="push",
                    created_at=now - timedelta(hours=16),
                ),
                CheckInEvent(
                    id="ci-3",
                    owner_id=owner.id,
                    status="acknowledged",
                    acknowledged_at=now - timedelta(hours=28),
                    method="webapp",
                    created_at=now - timedelta(hours=28),
                ),
            ]
        )

        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    seed_demo_data()
