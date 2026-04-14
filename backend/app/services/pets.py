from app.db.models import Pet
from app.schemas.pets import PetDTO, PetMedicalProfileDTO, VeterinarianDTO


def serialize_pet(pet: Pet) -> PetDTO:
    return PetDTO.model_validate(
        {
            "id": pet.id,
            "name": pet.name,
            "breed": pet.breed,
            "age_years": pet.age_years,
            "weight_kg": pet.weight_kg,
            "chip_number": pet.chip_number,
            "address": pet.address,
            "image_url": pet.image_url,
            "medical_profile": PetMedicalProfileDTO(
                pre_existing_conditions=pet.pre_existing_conditions,
                allergies=pet.allergies,
                medications=pet.medications,
                vaccination_status=pet.vaccination_status,
                insurance=pet.insurance,
            ),
            "veterinarian": VeterinarianDTO(
                name=pet.veterinarian_name,
                phone=pet.veterinarian_phone,
            ),
            "feeding_notes": pet.feeding_notes,
            "special_needs": pet.special_needs,
            "spare_key_location": pet.spare_key_location,
        }
    )
