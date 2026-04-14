from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import DbSession
from app.core.config import get_settings
from app.db.models import Owner
from app.repositories import responder as responder_repo
from app.repositories.check_in import get_active_escalation
from app.repositories.pets import get_pet_by_access_token
from app.schemas.emergency_profile import EmergencyProfileDTO
from app.schemas.public import ResponderAckRequest, ResponderAckResponse
from app.services.auth import generate_id
from app.services.email import build_responder_ack_email, send_email
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


@router.post(
    "/emergency-profile/{token}/acknowledge",
    response_model=ResponderAckResponse,
)
def acknowledge_emergency(
    token: str,
    payload: ResponderAckRequest,
    session: DbSession,
) -> ResponderAckResponse:
    pet = get_pet_by_access_token(session, token)
    if pet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notfallprofil nicht gefunden.",
        )

    active_escalation = get_active_escalation(session, pet.owner_id)
    if active_escalation is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Keine aktive Eskalation fuer dieses Profil.",
        )

    if responder_repo.has_acknowledged(session, active_escalation.id, payload.email):
        return ResponderAckResponse(success=True)

    responder_repo.create_acknowledgment(
        session,
        ack_id=generate_id(),
        escalation_event_id=active_escalation.id,
        pet_id=pet.id,
        responder_email=payload.email,
        responder_name=payload.name,
    )
    session.commit()

    # Notify owner (best-effort, don't fail on email error).
    try:
        owner = session.scalar(select(Owner).where(Owner.id == pet.owner_id))
        if owner:
            settings = get_settings()
            responder_label = payload.name or payload.email
            subject, body = build_responder_ack_email(
                owner_name=owner.display_name,
                responder_name=responder_label,
                pet_name=pet.name,
                app_url=settings.app_url,
            )
            send_email(to=owner.email, subject=subject, body=body)
    except Exception:
        pass  # best-effort

    return ResponderAckResponse(success=True)
