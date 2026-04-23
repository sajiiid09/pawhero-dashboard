from __future__ import annotations

import json
import logging

from pywebpush import WebPushException, webpush
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import ContactPushSubscription
from app.repositories import contact_push as contact_push_repo
from app.services.auth import generate_id
from app.services.push import (
    PUSH_FAILURE_DELIVERY_FAILED,
    PUSH_FAILURE_INTEGRATION_ERROR,
    PUSH_FAILURE_NO_ACTIVE_SUBSCRIPTIONS,
    PUSH_FAILURE_PARTIAL_DELIVERY,
    PUSH_FAILURE_VAPID_NOT_CONFIGURED,
    PushResult,
    build_push_payload,
    build_subscription_info,
)

logger = logging.getLogger(__name__)


def normalize_contact_email(email: str) -> str:
    return email.lower().strip()


def save_contact_subscription(
    session: Session,
    *,
    email: str,
    endpoint: str,
    p256dh: str,
    auth: str,
    user_agent: str | None,
) -> ContactPushSubscription:
    normalized_email = normalize_contact_email(email)
    logger.info("saving contact push subscription email=%s endpoint=%s", normalized_email, endpoint)
    return contact_push_repo.upsert_subscription(
        session,
        sub_id=generate_id(),
        email=normalized_email,
        endpoint=endpoint,
        p256dh=p256dh,
        auth=auth,
        user_agent=user_agent,
    )


def list_contact_push_endpoints(session: Session, email: str) -> list[str]:
    normalized_email = normalize_contact_email(email)
    return contact_push_repo.list_active_endpoints_by_email(session, normalized_email)


def revoke_contact_subscription(session: Session, *, email: str, endpoint: str) -> bool:
    normalized_email = normalize_contact_email(email)
    found = contact_push_repo.revoke_by_email_and_endpoint(session, normalized_email, endpoint)
    if found:
        logger.info(
            "revoked contact push subscription email=%s endpoint=%s",
            normalized_email,
            endpoint,
        )
    else:
        logger.info(
            "contact push subscription not found for revoke email=%s endpoint=%s",
            normalized_email,
            endpoint,
        )
    return found


def send_push_to_contact(
    session: Session,
    email: str,
    title: str,
    body: str,
    url: str = "/dashboard",
    *,
    category: str = "emergency_profile",
    tag: str | None = None,
    renotify: bool = False,
    require_interaction: bool = True,
) -> PushResult:
    settings = get_settings()

    if not settings.vapid_private_key or not settings.vapid_public_key:
        logger.warning("VAPID keys not configured, skipping contact push delivery")
        return PushResult(failure_count=1, failure_reason=PUSH_FAILURE_VAPID_NOT_CONFIGURED)

    normalized_email = normalize_contact_email(email)
    subs = contact_push_repo.list_active_by_email(session, normalized_email)
    if not subs:
        logger.info("no active contact push subscriptions for email=%s", normalized_email)
        return PushResult(failure_count=1, failure_reason=PUSH_FAILURE_NO_ACTIVE_SUBSCRIPTIONS)

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
    unexpected_error = False
    logger.info(
        "sending contact push email=%s active_subscriptions=%d",
        normalized_email,
        len(subs),
    )

    for sub in subs:
        try:
            webpush(
                subscription_info=build_subscription_info(sub.endpoint, sub.p256dh, sub.auth),
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims=vapid_claims,
            )
            success += 1
        except WebPushException as exc:
            logger.warning("contact push failed for sub %s: %s", sub.id, exc)
            failure += 1
            response = getattr(exc, "response", None)
            status_code = getattr(response, "status_code", None)
            if status_code in (404, 410):
                contact_push_repo.mark_revoked(session, sub)
        except Exception:
            logger.exception("unexpected contact push error for sub %s", sub.id)
            failure += 1
            unexpected_error = True

    failure_reason: str | None = None
    if success == 0 and failure > 0:
        failure_reason = (
            PUSH_FAILURE_INTEGRATION_ERROR if unexpected_error else PUSH_FAILURE_DELIVERY_FAILED
        )
    elif success > 0 and failure > 0:
        failure_reason = PUSH_FAILURE_PARTIAL_DELIVERY

    logger.info(
        "contact push finished email=%s success=%d failure=%d",
        normalized_email,
        success,
        failure,
    )
    return PushResult(success_count=success, failure_count=failure, failure_reason=failure_reason)
