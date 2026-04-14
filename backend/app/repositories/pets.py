from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from app.db.models import Pet
from app.schemas.pets import PetUpsertRequest
from app.services.auth import generate_id


def list_pets(session: Session, owner_id: str) -> list[Pet]:
    statement: Select[tuple[Pet]] = (
        select(Pet).where(Pet.owner_id == owner_id).order_by(desc(Pet.created_at))
    )
    return list(session.scalars(statement))


def get_pet(session: Session, owner_id: str, pet_id: str) -> Pet | None:
    statement = select(Pet).where(Pet.owner_id == owner_id, Pet.id == pet_id)
    return session.scalar(statement)


def get_pet_by_access_token(session: Session, token: str) -> Pet | None:
    return session.scalar(select(Pet).where(Pet.emergency_access_token == token))


def save_pet(session: Session, owner_id: str, pet_id: str, payload: PetUpsertRequest) -> Pet:
    pet = get_pet(session, owner_id, pet_id)

    if pet is None:
        pet = Pet(id=pet_id, owner_id=owner_id, emergency_access_token=generate_id())
        session.add(pet)

    pet.name = payload.name
    pet.breed = payload.breed
    pet.age_years = payload.age_years
    pet.weight_kg = payload.weight_kg
    pet.chip_number = payload.chip_number
    pet.address = payload.address
    pet.image_url = payload.image_url
    pet.pre_existing_conditions = payload.medical_profile.pre_existing_conditions
    pet.allergies = payload.medical_profile.allergies
    pet.medications = payload.medical_profile.medications
    pet.vaccination_status = payload.medical_profile.vaccination_status
    pet.insurance = payload.medical_profile.insurance
    pet.veterinarian_name = payload.veterinarian.name
    pet.veterinarian_phone = payload.veterinarian.phone
    pet.feeding_notes = payload.feeding_notes
    pet.special_needs = payload.special_needs
    pet.spare_key_location = payload.spare_key_location

    session.flush()
    session.refresh(pet)
    return pet


def delete_pet(session: Session, owner_id: str, pet_id: str) -> bool:
    pet = get_pet(session, owner_id, pet_id)
    if pet is None:
        return False

    session.delete(pet)
    session.flush()
    return True
