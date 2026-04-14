from pydantic import Field

from app.schemas.common import AppSchema
from app.schemas.emergency_chain import EmergencyChainContactDTO
from app.schemas.pets import PetDTO


class EscalationContextDTO(AppSchema):
    started_at: str = Field(alias="startedAt")
    acknowledgment_count: int = Field(alias="acknowledgmentCount")


class EmergencyProfileDTO(AppSchema):
    pet: PetDTO
    profile_id: str = Field(alias="profileId")
    important_notes: list[str] = Field(alias="importantNotes")
    contacts: list[EmergencyChainContactDTO]
    medical_record: list[str] = Field(alias="medicalRecord")
    help_text: str = Field(alias="helpText")
    escalation_context: EscalationContextDTO | None = Field(alias="escalationContext", default=None)
    feeding_notes: str = Field(alias="feedingNotes", default="")
    spare_key_location: str = Field(alias="spareKeyLocation", default="")
