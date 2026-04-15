from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import DbSession
from app.core.config import get_settings
from app.db.models import NotificationChannel, NotificationType, Owner
from app.repositories import notification as notification_repo
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

    _notify_owner_about_responder_ack(
        session=session,
        owner_id=pet.owner_id,
        escalation_event_id=active_escalation.id,
        pet_name=pet.name,
        responder_name=payload.name or payload.email,
    )

    return ResponderAckResponse(success=True)


def _notify_owner_about_responder_ack(
    *,
    session: DbSession,
    owner_id: str,
    escalation_event_id: str,
    pet_name: str,
    responder_name: str,
) -> None:
    owner = session.scalar(select(Owner).where(Owner.id == owner_id))
    if owner is None:
        return

    settings = get_settings()
    subject, body = build_responder_ack_email(
        owner_name=owner.display_name,
        responder_name=responder_name,
        pet_name=pet_name,
        app_url=settings.app_url,
    )

    status_value = "sent"
    error_message = None
    try:
        send_email(to=owner.email, subject=subject, body=body)
    except Exception as exc:
        status_value = "failed"
        error_message = str(exc)[:500]

    notification_repo.create_notification_log(
        session,
        log_id=generate_id(),
        owner_id=owner_id,
        escalation_event_id=escalation_event_id,
        recipient_email=owner.email,
        channel=NotificationChannel.EMAIL,
        notification_type=NotificationType.RESPONDER_ACKNOWLEDGMENT,
        status=status_value,
        error_message=error_message,
    )
    session.commit()
