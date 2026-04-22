from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import DbSession, OwnerId
from app.core.config import get_settings
from app.schemas.push import (
    PushDiagnosticsDTO,
    PushPreviewResultDTO,
    PushSubscriptionDTO,
    SavePushSubscriptionRequest,
)
from app.services import push as push_service

router = APIRouter(prefix="/push", tags=["push"])


@router.get("/vapid-public-key")
def read_vapid_public_key() -> dict[str, str]:
    settings = get_settings()
    return {"publicKey": settings.vapid_public_key}


@router.get("/subscriptions", response_model=list[PushSubscriptionDTO])
def list_push_subscriptions(session: DbSession, owner_id: OwnerId) -> list[PushSubscriptionDTO]:
    return push_service.list_subscriptions(session, owner_id)


@router.post("/subscriptions", response_model=PushSubscriptionDTO)
def save_push_subscription(
    payload: SavePushSubscriptionRequest,
    session: DbSession,
    owner_id: OwnerId,
) -> PushSubscriptionDTO:
    result = push_service.save_subscription(
        session,
        owner_id=owner_id,
        endpoint=payload.endpoint,
        p256dh=payload.p256dh,
        auth_key=payload.auth,
        user_agent=payload.user_agent,
    )
    session.commit()
    return result


@router.delete("/subscriptions", status_code=status.HTTP_204_NO_CONTENT)
def revoke_push_subscription(
    payload: SavePushSubscriptionRequest,
    session: DbSession,
    owner_id: OwnerId,
) -> None:
    revoked = push_service.revoke_subscription(session, owner_id, payload.endpoint)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kein aktives Push-Abonnement fuer diesen Endpunkt gefunden.",
        )
    session.commit()


@router.post("/preview", response_model=PushPreviewResultDTO)
def send_push_preview(session: DbSession, owner_id: OwnerId) -> PushPreviewResultDTO:
    result = push_service.send_push_preview(session, owner_id)
    session.commit()
    return result


@router.get("/diagnostics", response_model=PushDiagnosticsDTO)
def read_push_diagnostics(session: DbSession, owner_id: OwnerId) -> PushDiagnosticsDTO:
    return push_service.get_push_diagnostics(session, owner_id)
