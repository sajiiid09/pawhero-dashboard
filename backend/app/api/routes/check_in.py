from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import DbSession, OwnerId
from app.repositories.check_in import (
    get_check_in_config,
    list_check_in_events,
    list_escalation_history,
)
from app.schemas.check_in import (
    CheckInConfigDTO,
    CheckInConfigUpdateRequest,
    CheckInEventDTO,
    CheckInStatusDTO,
    EscalationEventDTO,
)
from app.services.check_in import (
    acknowledge_check_in,
    get_check_in_status,
    save_check_in_config,
    serialize_check_in_config,
    serialize_escalation_event,
)

router = APIRouter(tags=["check-in"])


@router.get("/check-in-config", response_model=CheckInConfigDTO)
def read_check_in_config(session: DbSession, owner_id: OwnerId) -> CheckInConfigDTO:
    config = get_check_in_config(session, owner_id)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check-in configuration not found.",
        )
    return serialize_check_in_config(config)


@router.put("/check-in-config", response_model=CheckInConfigDTO)
def update_check_in_config(
    payload: CheckInConfigUpdateRequest,
    session: DbSession,
    owner_id: OwnerId,
) -> CheckInConfigDTO:
    config = save_check_in_config(session, owner_id, payload)
    session.commit()
    return serialize_check_in_config(config)


@router.post("/check-in/acknowledge", response_model=CheckInStatusDTO)
def acknowledge(session: DbSession, owner_id: OwnerId) -> CheckInStatusDTO:
    result = acknowledge_check_in(session, owner_id)
    session.commit()
    return result


@router.get("/check-in/status", response_model=CheckInStatusDTO | None)
def read_check_in_status(session: DbSession, owner_id: OwnerId) -> CheckInStatusDTO | None:
    result = get_check_in_status(session, owner_id)
    if result is not None:
        session.commit()
    return result


@router.get("/check-in/events", response_model=list[CheckInEventDTO])
def read_check_in_events(session: DbSession, owner_id: OwnerId) -> list[CheckInEventDTO]:
    events = list_check_in_events(session, owner_id)
    return [
        CheckInEventDTO(
            id=e.id,
            status=e.status,
            acknowledged_at=e.acknowledged_at.isoformat(),
            method=e.method,
        )
        for e in events
    ]


@router.get("/check-in/escalation-history", response_model=list[EscalationEventDTO])
def read_escalation_history(session: DbSession, owner_id: OwnerId) -> list[EscalationEventDTO]:
    events = list_escalation_history(session, owner_id)
    return [serialize_escalation_event(e) for e in events]
