from __future__ import annotations

from pydantic import Field

from app.schemas.common import AppSchema


class PublicCheckInStatusDTO(AppSchema):
    mode: str
    escalation_deadline: str | None = Field(alias="escalationDeadline", default=None)
    next_check_in_at: str = Field(alias="nextCheckInAt")
    owner_name: str = Field(alias="ownerName")
    acknowledged: bool = Field(default=False)


class PublicCheckInAckResponse(AppSchema):
    success: bool
    already_acknowledged: bool = Field(alias="alreadyAcknowledged", default=False)
