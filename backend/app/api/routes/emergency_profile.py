from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import DbSession, OwnerId
from app.schemas.emergency_profile import EmergencyProfileDTO
from app.services.emergency_profile import build_emergency_profile

router = APIRouter(prefix="/pets", tags=["emergency-profile"])


@router.get("/{pet_id}/emergency-profile", response_model=EmergencyProfileDTO)
def get_emergency_profile(pet_id: str, session: DbSession, owner_id: OwnerId) -> EmergencyProfileDTO:
    profile = build_emergency_profile(session, owner_id, pet_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency profile not found.",
        )
    return profile
