from pydantic import Field

from app.schemas.common import AppSchema


class CheckInConfigDTO(AppSchema):
    interval_hours: int = Field(alias="intervalHours")
    escalation_delay_minutes: int = Field(alias="escalationDelayMinutes")
    primary_method: str = Field(alias="primaryMethod")
    backup_method: str = Field(alias="backupMethod")
    next_scheduled_at: str = Field(alias="nextScheduledAt")


class CheckInConfigUpdateRequest(AppSchema):
    interval_hours: int = Field(alias="intervalHours")
    escalation_delay_minutes: int = Field(alias="escalationDelayMinutes")
    primary_method: str = Field(alias="primaryMethod")
    backup_method: str = Field(alias="backupMethod")
