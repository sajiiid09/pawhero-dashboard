from pydantic import Field

from app.schemas.common import AppSchema


class CheckInConfigDTO(AppSchema):
    interval_hours: int = Field(alias="intervalHours")
    escalation_delay_minutes: int = Field(alias="escalationDelayMinutes")
    push_enabled: bool = Field(alias="pushEnabled")
    email_enabled: bool = Field(alias="emailEnabled")
    next_scheduled_at: str = Field(alias="nextScheduledAt")


class CheckInConfigUpdateRequest(AppSchema):
    interval_hours: int = Field(alias="intervalHours")
    escalation_delay_minutes: int = Field(alias="escalationDelayMinutes")
    push_enabled: bool = Field(alias="pushEnabled")
    email_enabled: bool = Field(alias="emailEnabled")


class CheckInStatusDTO(AppSchema):
    mode: str
    escalation_deadline: str | None = Field(alias="escalationDeadline", default=None)
    next_check_in_at: str = Field(alias="nextCheckInAt")


class CheckInEventDTO(AppSchema):
    id: str
    status: str
    acknowledged_at: str = Field(alias="acknowledgedAt")
    method: str


class EscalationEventDTO(AppSchema):
    id: str
    started_at: str = Field(alias="startedAt")
    resolved_at: str | None = Field(alias="resolvedAt", default=None)
