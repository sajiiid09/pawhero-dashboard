from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from pywebpush import WebPushException, webpush
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import PushSubscription
from app.repositories import push as push_repo
from app.schemas.push import PushPreviewResultDTO, PushSubscriptionDTO
from app.services.auth import generate_id

logger = logging.getLogger(__name__)


@dataclass
class PushResult:
    success_count: int = 0
    failure_count: int = 0
    failure_reason: str | None = None


def serialize_push_subscription(sub: PushSubscription) -> PushSubscriptionDTO:
    return PushSubscriptionDTO(
        id=sub.id,
        endpoint=sub.endpoint,
        user_agent=sub.user_agent,
        created_at=sub.created_at.isoformat(),
        last_seen_at=sub.last_seen_at.isoformat(),
    )


def save_subscription(
    session: Session,
    owner_id: str,
    endpoint: str,
    p256dh: str,
    auth_key: str,
    user_agent: str | None,
) -> PushSubscriptionDTO:
    sub = push_repo.upsert_subscription(
        session,
        sub_id=generate_id(),
        owner_id=owner_id,
        endpoint=endpoint,
        p256dh=p256dh,
        auth=auth_key,
        user_agent=user_agent,
    )
    return serialize_push_subscription(sub)


def revoke_subscription(session: Session, owner_id: str, endpoint: str) -> bool:
    return push_repo.revoke_subscription_by_endpoint(session, owner_id, endpoint)


def list_subscriptions(session: Session, owner_id: str) -> list[PushSubscriptionDTO]:
    subs = push_repo.list_active_subscriptions(session, owner_id)
    return [serialize_push_subscription(sub) for sub in subs]


def send_push_to_owner(
    session: Session,
    owner_id: str,
    title: str,
    body: str,
    url: str = "/dashboard",
) -> PushResult:
    settings = get_settings()

    if not settings.vapid_private_key or not settings.vapid_public_key:
        logger.warning("VAPID keys not configured, skipping push delivery")
        return PushResult(failure_count=1, failure_reason="vapid_not_configured")

    subs = push_repo.list_active_subscriptions(session, owner_id)
    if not subs:
        logger.info("no active push subscriptions for owner_id=%s", owner_id)
        return PushResult(failure_count=1, failure_reason="no_active_subscriptions")

    payload = json.dumps({"title": title, "body": body, "url": url})
    vapid_claims = {"sub": settings.vapid_subject}

    success = 0
    failure = 0

    for sub in subs:
        try:
            webpush(
                subscription={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims=vapid_claims,
            )
            success += 1
        except WebPushException as exc:
            logger.warning("push failed for sub %s: %s", sub.id, exc)
            failure += 1
            response = getattr(exc, "response", None)
            status_code = getattr(response, "status_code", None)
            if status_code in (404, 410):
                push_repo.mark_revoked(session, sub)
        except Exception:
            logger.exception("unexpected push error for sub %s", sub.id)
            failure += 1

    failure_reason: str | None = None
    if success == 0 and failure > 0:
        failure_reason = "delivery_failed"
    elif success > 0 and failure > 0:
        failure_reason = "partial_delivery"

    return PushResult(success_count=success, failure_count=failure, failure_reason=failure_reason)


def send_push_preview(session: Session, owner_id: str) -> PushPreviewResultDTO:
    result = send_push_to_owner(
        session,
        owner_id,
        title="Check-In Erinnerung",
        body="Bitte bestaetige jetzt im Dashboard, dass alles in Ordnung ist.",
        url="/check-in",
    )
    return PushPreviewResultDTO(
        success_count=result.success_count,
        failure_count=result.failure_count,
    )
