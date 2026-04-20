import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.api.dependencies import DbSession, OwnerId
from app.repositories.pets import get_pet, list_pets, save_pet
from app.schemas.pets import PetDTO, PetUpsertRequest
from app.services import storage
from app.services.auth import generate_id
from app.services.pets import serialize_pet

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pets", tags=["pets"])


class EmergencyAccessTokenResponse(BaseModel):
    access_token: str


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
def update_pet(
    pet_id: str, payload: PetUpsertRequest, session: DbSession, owner_id: OwnerId
) -> PetDTO:
    existing_pet = get_pet(session, owner_id, pet_id)
    if existing_pet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found.")

    pet = save_pet(session, owner_id, pet_id, payload)
    session.commit()
    return serialize_pet(pet)


@router.post("/{pet_id}/image", response_model=PetDTO)
async def upload_pet_image(
    pet_id: str,
    file: UploadFile,
    session: DbSession,
    owner_id: OwnerId,
) -> PetDTO:
    pet = get_pet(session, owner_id, pet_id)
    if pet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found.")

    content_type = file.content_type or ""
    file_bytes = await file.read()
    file_size = len(file_bytes)

    try:
        storage.validate_image(content_type, file_size)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    try:
        public_url = storage.upload_image(pet_id, file_bytes, content_type)
    except Exception as exc:
        logger.exception("Image upload failed for pet %s", pet_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bild konnte nicht hochgeladen werden. Bitte erneut versuchen.",
        ) from exc

    old_url = pet.image_url
    pet.image_url = public_url
    session.flush()

    if old_url and not old_url.startswith("data:"):
        storage.delete_image(old_url)

    session.commit()
    return serialize_pet(pet)


@router.delete("/{pet_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_pet(pet_id: str, session: DbSession, owner_id: OwnerId) -> None:
    pet = get_pet(session, owner_id, pet_id)
    if pet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found.")

    # Clean up storage assets before DB deletion
    if pet.image_url and not pet.image_url.startswith("data:"):
        storage.delete_image(pet.image_url)

    for doc in pet.documents:
        storage.delete_document(doc.storage_key)

    session.delete(pet)
    session.flush()
    session.commit()


@router.get(
    "/{pet_id}/emergency-access-token",
    response_model=EmergencyAccessTokenResponse,
)
def get_emergency_access_token(
    pet_id: str, session: DbSession, owner_id: OwnerId
) -> EmergencyAccessTokenResponse:
    pet = get_pet(session, owner_id, pet_id)
    if pet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found.")

    if not pet.emergency_access_token:
        pet.emergency_access_token = generate_id()
        session.flush()

    return EmergencyAccessTokenResponse(access_token=pet.emergency_access_token)


@router.post(
    "/{pet_id}/emergency-access-token/regenerate",
    response_model=EmergencyAccessTokenResponse,
)
def regenerate_emergency_access_token(
    pet_id: str, session: DbSession, owner_id: OwnerId
) -> EmergencyAccessTokenResponse:
    pet = get_pet(session, owner_id, pet_id)
    if pet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found.")

    pet.emergency_access_token = generate_id()
    session.flush()
    return EmergencyAccessTokenResponse(access_token=pet.emergency_access_token)
