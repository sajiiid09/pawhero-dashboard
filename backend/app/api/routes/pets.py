from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import DbSession, OwnerId
from app.repositories.pets import delete_pet, get_pet, list_pets, save_pet
from app.schemas.pets import PetDTO, PetUpsertRequest
from app.services.pets import serialize_pet

router = APIRouter(prefix="/pets", tags=["pets"])


@router.get("", response_model=list[PetDTO])
def get_pets(session: DbSession, owner_id: OwnerId) -> list[PetDTO]:
    return [serialize_pet(pet) for pet in list_pets(session, owner_id)]


@router.post("", response_model=PetDTO, status_code=status.HTTP_201_CREATED)
def create_pet(payload: PetUpsertRequest, session: DbSession, owner_id: OwnerId) -> PetDTO:
    pet = save_pet(session, owner_id, f"pet-{uuid4().hex}", payload)
    session.commit()
    return serialize_pet(pet)


@router.get("/{pet_id}", response_model=PetDTO)
def get_pet_by_id(pet_id: str, session: DbSession, owner_id: OwnerId) -> PetDTO:
    pet = get_pet(session, owner_id, pet_id)
    if pet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found.")
    return serialize_pet(pet)


@router.put("/{pet_id}", response_model=PetDTO)
def update_pet(pet_id: str, payload: PetUpsertRequest, session: DbSession, owner_id: OwnerId) -> PetDTO:
    existing_pet = get_pet(session, owner_id, pet_id)
    if existing_pet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found.")

    pet = save_pet(session, owner_id, pet_id, payload)
    session.commit()
    return serialize_pet(pet)


@router.delete("/{pet_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_pet(pet_id: str, session: DbSession, owner_id: OwnerId) -> None:
    was_deleted = delete_pet(session, owner_id, pet_id)
    if not was_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found.")
    session.commit()
