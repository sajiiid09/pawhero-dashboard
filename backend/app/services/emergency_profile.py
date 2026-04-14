from sqlalchemy.orm import Session

from app.repositories import emergency_chain as emergency_chain_repository
from app.repositories.pets import get_pet
from app.schemas.emergency_profile import EmergencyProfileDTO
from app.services.emergency_chain import list_chain_contacts
from app.services.pets import serialize_pet


def build_emergency_profile(session: Session, owner_id: str, pet_id: str) -> EmergencyProfileDTO | None:
    pet = get_pet(session, owner_id, pet_id)
    if pet is None:
        return None

    contacts = list_chain_contacts(session, owner_id)
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
        }
    )
