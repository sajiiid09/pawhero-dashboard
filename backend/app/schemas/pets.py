from pydantic import Field

from app.schemas.common import AppSchema


class PetMedicalProfileDTO(AppSchema):
    pre_existing_conditions: str = Field(alias="preExistingConditions")
    allergies: str
    medications: str
    vaccination_status: str = Field(alias="vaccinationStatus")
    insurance: str


class VeterinarianDTO(AppSchema):
    name: str
    phone: str


class PetDTO(AppSchema):
    id: str
    name: str
    breed: str
    age_years: int = Field(alias="ageYears")
    weight_kg: float = Field(alias="weightKg")
    chip_number: str = Field(alias="chipNumber")
    address: str
    image_url: str | None = Field(alias="imageUrl")
    medical_profile: PetMedicalProfileDTO = Field(alias="medicalProfile")
    veterinarian: VeterinarianDTO
    feeding_notes: str = Field(alias="feedingNotes")
    special_needs: str = Field(alias="specialNeeds")
    spare_key_location: str = Field(alias="spareKeyLocation")


class PetUpsertRequest(AppSchema):
    name: str
    breed: str
    age_years: int = Field(alias="ageYears")
    weight_kg: float = Field(alias="weightKg")
    chip_number: str = Field(alias="chipNumber")
    address: str
    image_url: str | None = Field(default=None, alias="imageUrl")
    medical_profile: PetMedicalProfileDTO = Field(alias="medicalProfile")
    veterinarian: VeterinarianDTO
    feeding_notes: str = Field(alias="feedingNotes")
    special_needs: str = Field(alias="specialNeeds")
    spare_key_location: str = Field(alias="spareKeyLocation")
