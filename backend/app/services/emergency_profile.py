from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Pet
from app.repositories import responder as responder_repo
from app.repositories.check_in import get_active_escalation, get_check_in_config
from app.repositories.pets import get_pet
from app.schemas.emergency_profile import EmergencyProfileDTO
from app.services.check_in import EscalationMode, compute_escalation_state
from app.services.emergency_chain import list_chain_contacts
from app.services.pets import serialize_pet


def _build_profile(
    pet: Pet,
    contacts: list[dict],
    escalation_context: dict | None = None,
) -> EmergencyProfileDTO:
    important_notes = [
        pet.allergies or "Keine bekannten Allergien",
        pet.medications or "Keine taeglichen Medikamente",
        pet.special_needs or pet.feeding_notes,
    ]
    medical_record = [
        f"Krankenakte: {pet.pre_existing_conditions}",
        f"Impfstatus: {pet.vaccination_status}",
        f"Versicherung: {pet.insurance}",
        f"Tierarzt: {pet.veterinarian_name} ({pet.veterinarian_phone})",
    ]

    return EmergencyProfileDTO.model_validate(
        {
            "pet": serialize_pet(pet),
            "profile_id": pet.chip_number,
            "important_notes": [note for note in important_notes if note],
            "contacts": contacts,
            "medical_record": medical_record,
            "help_text": (
                "Bitte zuerst die hinterlegten Kontaktpersonen anrufen. "
                "Falls niemand erreichbar ist, danach das oertliche Tierheim kontaktieren."
            ),
            "escalation_context": escalation_context,
            "feeding_notes": pet.feeding_notes,
            "spare_key_location": pet.spare_key_location,
        }
    )


def _build_escalation_context(session: Session, pet: Pet) -> dict | None:
    config = get_check_in_config(session, pet.owner_id)
    if config is None:
        return None

    mode, _deadline = compute_escalation_state(config)
    if mode != EscalationMode.ESCALATED:
        return None

    active = get_active_escalation(session, pet.owner_id)
    if active is None:
        return None

    ack_count = responder_repo.count_acknowledgments(session, active.id)

    return {
        "startedAt": active.started_at.isoformat(),
        "acknowledgmentCount": ack_count,
    }


def build_emergency_profile(
    session: Session, owner_id: str, pet_id: str
) -> EmergencyProfileDTO | None:
    pet = get_pet(session, owner_id, pet_id)
    if pet is None:
        return None

    contacts = list_chain_contacts(session, owner_id)
    return _build_profile(pet, contacts)


def build_emergency_profile_for_pet(session: Session, pet: Pet) -> EmergencyProfileDTO:
    contacts = list_chain_contacts(session, pet.owner_id)
    escalation_context = _build_escalation_context(session, pet)
    return _build_profile(pet, contacts, escalation_context)
