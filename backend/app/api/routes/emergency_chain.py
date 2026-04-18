from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import DbSession, OwnerId
from app.repositories import emergency_chain as emergency_chain_repository
from app.schemas.emergency_chain import (
    EmergencyChainContactDTO,
    EmergencyContactUpsertRequest,
    MoveEmergencyContactRequest,
)
from app.services.emergency_chain import list_chain_contacts, move_contact, serialize_chain_contact

router = APIRouter(prefix="/emergency-chain", tags=["emergency-chain"])


@router.get("", response_model=list[EmergencyChainContactDTO])
def get_emergency_chain(session: DbSession, owner_id: OwnerId) -> list[EmergencyChainContactDTO]:
    return list_chain_contacts(session, owner_id)


@router.post(
    "/contacts",
    response_model=EmergencyChainContactDTO,
    status_code=status.HTTP_201_CREATED,
)
def create_emergency_contact(
    payload: EmergencyContactUpsertRequest,
    session: DbSession,
    owner_id: OwnerId,
) -> EmergencyChainContactDTO:
    contact_id = f"contact-{uuid4().hex}"
    contact = emergency_chain_repository.save_contact(session, owner_id, contact_id, payload)
    emergency_chain_repository.normalize_priorities(session, owner_id)
    session.commit()
    entry = emergency_chain_repository.get_chain_entry(session, owner_id, contact.id)
    return serialize_chain_contact(contact, entry.priority if entry else payload.priority)


@router.get("/contacts/{contact_id}", response_model=EmergencyChainContactDTO)
def get_emergency_contact(
    contact_id: str,
    session: DbSession,
    owner_id: OwnerId,
) -> EmergencyChainContactDTO:
    contact = emergency_chain_repository.get_contact(session, owner_id, contact_id)
    entry = emergency_chain_repository.get_chain_entry(session, owner_id, contact_id)
    if contact is None or entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency contact not found.",
        )
    return serialize_chain_contact(contact, entry.priority)


@router.put("/contacts/{contact_id}", response_model=EmergencyChainContactDTO)
def update_emergency_contact(
    contact_id: str,
    payload: EmergencyContactUpsertRequest,
    session: DbSession,
    owner_id: OwnerId,
) -> EmergencyChainContactDTO:
    existing = emergency_chain_repository.get_contact(session, owner_id, contact_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency contact not found.",
        )
    contact = emergency_chain_repository.save_contact(session, owner_id, contact_id, payload)
    emergency_chain_repository.normalize_priorities(session, owner_id)
    session.commit()
    entry = emergency_chain_repository.get_chain_entry(session, owner_id, contact.id)
    return serialize_chain_contact(contact, entry.priority if entry else payload.priority)


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_emergency_contact(contact_id: str, session: DbSession, owner_id: OwnerId) -> None:
    deleted = emergency_chain_repository.delete_contact(session, owner_id, contact_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency contact not found.",
        )
    emergency_chain_repository.normalize_priorities(session, owner_id)
    session.commit()


@router.post("/contacts/{contact_id}/move", response_model=list[EmergencyChainContactDTO])
def move_emergency_contact(
    contact_id: str,
    payload: MoveEmergencyContactRequest,
    session: DbSession,
    owner_id: OwnerId,
) -> list[EmergencyChainContactDTO]:
    if payload.direction not in {"up", "down"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid direction.")

    try:
        move_contact(session, owner_id, contact_id, payload.direction)
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error

    session.commit()
    return list_chain_contacts(session, owner_id)
