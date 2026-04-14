from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import DbSession
from app.repositories.pets import get_pet_by_access_token
from app.schemas.emergency_profile import EmergencyProfileDTO
from app.services.emergency_profile import build_emergency_profile_for_pet

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/emergency-profile/{token}", response_model=EmergencyProfileDTO)
def get_public_emergency_profile(token: str, session: DbSession) -> EmergencyProfileDTO:
    pet = get_pet_by_access_token(session, token)
    if pet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notfallprofil nicht gefunden.",
        )

    profile = build_emergency_profile_for_pet(session, pet)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notfallprofil nicht gefunden.",
        )
    return profile
