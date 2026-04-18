from sqlalchemy.orm import Session

from app.repositories import emergency_chain as emergency_chain_repository
from app.schemas.emergency_chain import EmergencyChainContactDTO


def serialize_chain_contact(contact, priority: int) -> EmergencyChainContactDTO:
    return EmergencyChainContactDTO.model_validate(
        {
            "id": contact.id,
            "name": contact.name,
            "relationship": contact.relationship_label,
            "phone": contact.phone,
            "email": contact.email,
            "has_apartment_key": contact.has_apartment_key,
            "can_take_dog": contact.can_take_dog,
            "notes": contact.notes,
            "priority": priority,
        }
    )


def list_chain_contacts(session: Session, owner_id: str) -> list[EmergencyChainContactDTO]:
    contacts = emergency_chain_repository.list_ordered_contacts(session, owner_id)
    return [serialize_chain_contact(contact, entry.priority) for contact, entry in contacts]


def move_contact(session: Session, owner_id: str, contact_id: str, direction: str) -> None:
    ordered_pairs = emergency_chain_repository.list_ordered_contacts(session, owner_id)
    ordered_entries = [entry for _, entry in ordered_pairs]
    index = next(
        (i for i, entry in enumerate(ordered_entries) if entry.contact_id == contact_id),
        -1,
    )

    if index == -1:
        raise LookupError("Emergency contact not found.")

    target_index = index - 1 if direction == "up" else index + 1
    if target_index < 0 or target_index >= len(ordered_entries):
        return

    reordered = list(ordered_entries)
    current = reordered.pop(index)
    reordered.insert(target_index, current)

    for position, entry in enumerate(reordered, start=1):
        entry.priority = position

    session.flush()
