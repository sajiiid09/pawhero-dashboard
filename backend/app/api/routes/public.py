from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import DbSession
from app.core.config import get_settings
from app.db.models import NotificationChannel, NotificationType, Owner
from app.repositories import notification as notification_repo
from app.repositories import responder as responder_repo
from app.repositories.check_in import get_active_escalation, get_check_in_config
from app.repositories.pets import get_pet_by_access_token
from app.schemas.contact_push import (
    ContactPushSubscribeRequest,
    ContactPushUnsubscribeRequest,
)
from app.schemas.emergency_profile import EmergencyProfileDTO
from app.schemas.public import ResponderAckRequest, ResponderAckResponse
from app.schemas.public_check_in import PublicCheckInAckResponse, PublicCheckInStatusDTO
from app.services.auth import generate_id
from app.services.check_in import EscalationMode, acknowledge_check_in, compute_escalation_state
from app.services.check_in_action_token import is_token_expired, lookup_token, mark_token_used
from app.services.contact_push import (
    revoke_contact_subscription,
    save_contact_subscription,
)
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


@router.get("/check-in/{token}", response_model=PublicCheckInStatusDTO)
def get_public_check_in_status(token: str, session: DbSession) -> PublicCheckInStatusDTO:
    action_token = lookup_token(session, token)
    if action_token is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check-In-Link nicht gefunden.",
        )

    if is_token_expired(action_token):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Dieser Check-In-Link ist abgelaufen.",
        )

    owner = session.scalar(select(Owner).where(Owner.id == action_token.owner_id))
    if owner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check-In-Link nicht gefunden.",
        )

    already_acknowledged = action_token.used_at is not None

    # If not yet acknowledged via this link, check if the owner already
    # acknowledged via dashboard (no active escalation + token unused).
    if not already_acknowledged:
        config = get_check_in_config(session, action_token.owner_id)
        if config is not None:
            mode, _ = compute_escalation_state(config)
            if mode == EscalationMode.NORMAL:
                already_acknowledged = True

    if already_acknowledged:
        config = get_check_in_config(session, action_token.owner_id)
        return PublicCheckInStatusDTO(
            mode="normal",
            escalation_deadline=None,
            next_check_in_at=config.next_scheduled_at.isoformat() if config else "",
            owner_name=owner.display_name,
            acknowledged=True,
        )

    config = get_check_in_config(session, action_token.owner_id)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keine Check-In-Konfiguration vorhanden.",
        )

    mode, deadline = compute_escalation_state(config)
    return PublicCheckInStatusDTO(
        mode=mode,
        escalation_deadline=deadline.isoformat() if deadline else None,
        next_check_in_at=config.next_scheduled_at.isoformat(),
        owner_name=owner.display_name,
        acknowledged=False,
    )


@router.post("/check-in/{token}/acknowledge", response_model=PublicCheckInAckResponse)
def acknowledge_public_check_in(
    token: str,
    session: DbSession,
) -> PublicCheckInAckResponse:
    action_token = lookup_token(session, token)
    if action_token is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check-In-Link nicht gefunden.",
        )

    if is_token_expired(action_token):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Dieser Check-In-Link ist abgelaufen.",
        )

    # Already used via this link — idempotent success.
    if action_token.used_at is not None:
        return PublicCheckInAckResponse(success=True, already_acknowledged=True)

    # Check if the owner already acknowledged via dashboard.
    config = get_check_in_config(session, action_token.owner_id)
    if config is not None:
        mode, _ = compute_escalation_state(config)
        if mode == EscalationMode.NORMAL:
            mark_token_used(action_token)
            session.commit()
            return PublicCheckInAckResponse(success=True, already_acknowledged=True)

    # Perform the acknowledgement.
    acknowledge_check_in(session, action_token.owner_id, method="public_link")
    mark_token_used(action_token)
    session.commit()

    return PublicCheckInAckResponse(success=True, already_acknowledged=False)


@router.post("/contact-push/subscribe")
def contact_push_subscribe(
    payload: ContactPushSubscribeRequest,
    session: DbSession,
) -> dict[str, bool]:
    save_contact_subscription(
        session,
        email=payload.email,
        endpoint=payload.endpoint,
        p256dh=payload.p256dh,
        auth=payload.auth,
        user_agent=payload.user_agent,
    )
    session.commit()
    return {"success": True}


@router.delete("/contact-push/subscribe")
def contact_push_unsubscribe(
    payload: ContactPushUnsubscribeRequest,
    session: DbSession,
) -> dict[str, bool]:
    found = revoke_contact_subscription(session, payload.endpoint)
    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Push-Abonnement nicht gefunden.",
        )
    session.commit()
    return {"success": True}
