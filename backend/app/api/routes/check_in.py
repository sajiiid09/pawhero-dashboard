from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import DbSession, OwnerId
from app.repositories.check_in import get_check_in_config
from app.schemas.check_in import CheckInConfigDTO, CheckInConfigUpdateRequest
from app.services.check_in import save_check_in_config, serialize_check_in_config

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
