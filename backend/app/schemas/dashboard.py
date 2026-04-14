from pydantic import Field

from app.schemas.common import AppSchema


class CheckInHistoryItemDTO(AppSchema):
    id: str
    status: str
    acknowledged_at: str = Field(alias="acknowledgedAt")
    method: str


class EscalationStatusDTO(AppSchema):
    mode: str
    title: str
    description: str
    escalation_deadline: str | None = Field(alias="escalationDeadline", default=None)


class MonitoredPetDTO(AppSchema):
    id: str
    name: str
    breed: str
    age_years: int = Field(alias="ageYears")
    image_url: str | None = Field(alias="imageUrl")


class DashboardSummaryDTO(AppSchema):
    pet_count: int = Field(alias="petCount")
    emergency_chain_status: str = Field(alias="emergencyChainStatus")
    next_check_in_at: str = Field(alias="nextCheckInAt")
    recent_check_ins: list[CheckInHistoryItemDTO] = Field(alias="recentCheckIns")
    escalation_status: EscalationStatusDTO = Field(alias="escalationStatus")
    monitored_pet: MonitoredPetDTO | None = Field(alias="monitoredPet")
