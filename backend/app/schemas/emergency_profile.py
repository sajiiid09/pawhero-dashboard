from pydantic import Field

from app.schemas.common import AppSchema
from app.schemas.emergency_chain import EmergencyChainContactDTO
from app.schemas.pets import PetDTO


class EmergencyProfileDTO(AppSchema):
    pet: PetDTO
    profile_id: str = Field(alias="profileId")
    important_notes: list[str] = Field(alias="importantNotes")
    contacts: list[EmergencyChainContactDTO]
    medical_record: list[str] = Field(alias="medicalRecord")
    help_text: str = Field(alias="helpText")
