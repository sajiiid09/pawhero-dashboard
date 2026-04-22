from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from urllib.parse import urlparse

from pywebpush import WebPushException, webpush
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import CheckInConfig, NotificationChannel, NotificationLog, PushSubscription
from app.repositories import push as push_repo
from app.repositories.check_in import get_check_in_config
from app.schemas.push import (
    PushDiagnosticsDTO,
    PushLogDiagnosticsDTO,
    PushPreviewResultDTO,
    PushSubscriptionDTO,
)
from app.services.auth import generate_id
from app.services.check_in_action_token import generate_action_token

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


def build_owner_check_in_url(
    session: Session,
    owner_id: str,
    app_url: str,
    *,
    config: CheckInConfig | None = None,
) -> str | None:
    owner_config = config or get_check_in_config(session, owner_id)
    if owner_config is None:
        logger.warning("missing check-in config for owner push owner_id=%s", owner_id)
        return None

    raw_token = generate_action_token(session, owner_config)
    target_url = f"{app_url}/c/{raw_token}"
    logger.info(
        "generated owner push target owner_id=%s cycle=%s route=/c/<token>",
        owner_id,
        owner_config.next_scheduled_at.isoformat(),
    )
    return target_url


def send_push_to_owner(
    session: Session,
    owner_id: str,
    title: str,
    body: str,
    url: str = "/dashboard",
    *,
    category: str = "generic",
    tag: str | None = None,
    renotify: bool = False,
    require_interaction: bool = True,
) -> PushResult:
    settings = get_settings()

    if not settings.vapid_private_key or not settings.vapid_public_key:
        logger.warning("VAPID keys not configured, skipping push delivery")
        return PushResult(failure_count=1, failure_reason="vapid_not_configured")

    subs = push_repo.list_active_subscriptions(session, owner_id)
    if not subs:
        logger.info("no active push subscriptions for owner_id=%s", owner_id)
        return PushResult(failure_count=1, failure_reason="no_active_subscriptions")

    payload = json.dumps(
        build_push_payload(
            title=title,
            body=body,
            url=url,
            category=category,
            tag=tag,
            renotify=renotify,
            require_interaction=require_interaction,
        )
    )
    vapid_claims = {"sub": settings.vapid_subject}

    success = 0
    failure = 0
    logger.info(
        "sending owner push owner_id=%s active_subscriptions=%d target=%s tag=%s",
        owner_id,
        len(subs),
        summarize_push_target(url),
        tag or "<none>",
    )

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

    logger.info(
        "owner push finished owner_id=%s success=%d failure=%d reason=%s",
        owner_id,
        success,
        failure,
        failure_reason or "none",
    )
    return PushResult(success_count=success, failure_count=failure, failure_reason=failure_reason)


def send_push_preview(session: Session, owner_id: str) -> PushPreviewResultDTO:
    settings = get_settings()
    target_url = build_owner_check_in_url(session, owner_id, settings.app_url)
    if target_url is None:
        logger.warning("preview push skipped missing owner check-in target owner_id=%s", owner_id)
        return PushPreviewResultDTO(success_count=0, failure_count=1)

    result = send_push_to_owner(
        session,
        owner_id,
        title="Check-In Erinnerung",
        body="Bitte bestaetige jetzt direkt, dass alles in Ordnung ist.",
        url=target_url,
        category="check_in",
        tag=f"owner-preview:{owner_id}",
    )
    return PushPreviewResultDTO(
        success_count=result.success_count,
        failure_count=result.failure_count,
    )


def get_push_diagnostics(session: Session, owner_id: str) -> PushDiagnosticsDTO:
    config = get_check_in_config(session, owner_id)
    subscriptions = push_repo.list_active_subscriptions(session, owner_id)
    push_logs = list(
        session.scalars(
            select(NotificationLog)
            .where(
                NotificationLog.owner_id == owner_id,
                NotificationLog.channel == NotificationChannel.PUSH,
            )
            .order_by(desc(NotificationLog.created_at))
            .limit(20)
        )
    )

    last_success = next((log.created_at.isoformat() for log in push_logs if log.status == "sent"), None)
    last_failure_log = next((log for log in push_logs if log.status != "sent"), None)
    last_failure = last_failure_log.created_at.isoformat() if last_failure_log is not None else None
    last_failure_reason = last_failure_log.error_message if last_failure_log is not None else None

    return PushDiagnosticsDTO(
        push_enabled=(config.push_enabled if config is not None else False),
        active_subscription_count=len(subscriptions),
        last_success_at=last_success,
        last_failure_at=last_failure,
        last_failure_reason=last_failure_reason,
        recent_logs=[
            PushLogDiagnosticsDTO(
                id=log.id,
                notification_type=log.notification_type,
                status=log.status,
                error_message=log.error_message,
                created_at=log.created_at.isoformat(),
            )
            for log in push_logs
        ],
    )


def build_push_payload(
    *,
    title: str,
    body: str,
    url: str,
    category: str = "generic",
    tag: str | None = None,
    renotify: bool = False,
    require_interaction: bool = True,
) -> dict[str, str | bool]:
    payload: dict[str, str | bool] = {
        "title": title,
        "body": body,
        "url": url,
        "category": category,
        "renotify": renotify,
        "requireInteraction": require_interaction,
    }
    if tag:
        payload["tag"] = tag
    return payload


def summarize_push_target(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or url
    if path.startswith("/c/"):
        return "/c/<token>"
    return path
