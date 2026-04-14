from sqlalchemy import Select, asc, select
from sqlalchemy.orm import Session

from app.db.models import EmergencyChainEntry, EmergencyContact
from app.schemas.emergency_chain import EmergencyContactUpsertRequest


def list_ordered_contacts(session: Session, owner_id: str) -> list[tuple[EmergencyContact, EmergencyChainEntry]]:
    statement: Select[tuple[EmergencyContact, EmergencyChainEntry]] = (
        select(EmergencyContact, EmergencyChainEntry)
        .join(EmergencyChainEntry, EmergencyChainEntry.contact_id == EmergencyContact.id)
        .where(EmergencyContact.owner_id == owner_id, EmergencyChainEntry.owner_id == owner_id)
        .order_by(asc(EmergencyChainEntry.priority))
    )
    return list(session.execute(statement).all())


def get_contact(session: Session, owner_id: str, contact_id: str) -> EmergencyContact | None:
    statement = select(EmergencyContact).where(
        EmergencyContact.owner_id == owner_id,
        EmergencyContact.id == contact_id,
    )
    return session.scalar(statement)


def get_chain_entry(session: Session, owner_id: str, contact_id: str) -> EmergencyChainEntry | None:
    statement = select(EmergencyChainEntry).where(
        EmergencyChainEntry.owner_id == owner_id,
        EmergencyChainEntry.contact_id == contact_id,
    )
    return session.scalar(statement)


def save_contact(
    session: Session,
    owner_id: str,
    contact_id: str,
    payload: EmergencyContactUpsertRequest,
) -> EmergencyContact:
    contact = get_contact(session, owner_id, contact_id)

    if contact is None:
        contact = EmergencyContact(id=contact_id, owner_id=owner_id)
        session.add(contact)

    contact.name = payload.name
    contact.relationship_label = payload.relationship
    contact.phone = payload.phone
    contact.email = payload.email
    contact.has_apartment_key = payload.has_apartment_key
    contact.can_take_dog = payload.can_take_dog
    contact.notes = payload.notes
    session.flush()

    entry = get_chain_entry(session, owner_id, contact_id)
    if entry is None:
        entry = EmergencyChainEntry(
            id=f"entry-{contact_id}",
            owner_id=owner_id,
            contact_id=contact_id,
            priority=payload.priority,
        )
        session.add(entry)
    else:
        entry.priority = payload.priority

    session.flush()
    return contact


def delete_contact(session: Session, owner_id: str, contact_id: str) -> bool:
    contact = get_contact(session, owner_id, contact_id)
    if contact is None:
        return False

    session.delete(contact)
    session.flush()
    return True


def normalize_priorities(session: Session, owner_id: str) -> None:
    ordered_entries = (
        session.scalars(
            select(EmergencyChainEntry)
            .where(EmergencyChainEntry.owner_id == owner_id)
            .order_by(asc(EmergencyChainEntry.priority))
        )
        .all()
    )

    for index, entry in enumerate(ordered_entries, start=1):
        entry.priority = index

    session.flush()
