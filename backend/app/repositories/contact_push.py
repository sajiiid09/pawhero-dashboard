import logging
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import ContactPushSubscription

logger = logging.getLogger(__name__)


def upsert_subscription(
    session: Session,
    *,
    sub_id: str,
    email: str,
    endpoint: str,
    p256dh: str,
    auth: str,
    user_agent: str | None,
) -> ContactPushSubscription:
    existing = session.scalar(
        select(ContactPushSubscription).where(ContactPushSubscription.endpoint == endpoint)
    )

    if existing is not None:
        existing.email = email
        existing.p256dh = p256dh
        existing.auth = auth
        existing.user_agent = user_agent
        existing.last_seen_at = datetime.now(UTC)
        existing.revoked_at = None
        session.flush()
        return existing

    sub = ContactPushSubscription(
        id=sub_id,
        email=email,
        endpoint=endpoint,
        p256dh=p256dh,
        auth=auth,
        user_agent=user_agent,
        last_seen_at=datetime.now(UTC),
    )
    session.add(sub)
    session.flush()
    return sub


def list_active_by_email(session: Session, email: str) -> list[ContactPushSubscription]:
    return list(
        session.scalars(
            select(ContactPushSubscription).where(
                ContactPushSubscription.email == email,
                ContactPushSubscription.revoked_at.is_(None),
            )
        )
    )


def revoke_by_endpoint(session: Session, endpoint: str) -> bool:
    sub = session.scalar(
        select(ContactPushSubscription).where(
            ContactPushSubscription.endpoint == endpoint,
            ContactPushSubscription.revoked_at.is_(None),
        )
    )
    if sub is None:
        return False
    sub.revoked_at = datetime.now(UTC)
    session.flush()
    return True


def mark_revoked(session: Session, subscription: ContactPushSubscription) -> None:
    subscription.revoked_at = datetime.now(UTC)
    session.flush()


def delete_revoked_before(session: Session, cutoff: datetime) -> int:
    result = session.execute(
        delete(ContactPushSubscription).where(
            ContactPushSubscription.revoked_at.is_not(None),
            ContactPushSubscription.revoked_at < cutoff,
        )
    )
    return result.rowcount or 0
