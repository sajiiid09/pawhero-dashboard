import logging
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import PushSubscription

logger = logging.getLogger(__name__)


def upsert_subscription(
    session: Session,
    *,
    sub_id: str,
    owner_id: str,
    endpoint: str,
    p256dh: str,
    auth: str,
    user_agent: str | None,
) -> PushSubscription:
    existing = session.scalar(select(PushSubscription).where(PushSubscription.endpoint == endpoint))

    if existing is not None:
        previous_owner_id = existing.owner_id
        if previous_owner_id != owner_id:
            logger.info(
                "transferring push endpoint between owners "
                "endpoint=%s from_owner_id=%s to_owner_id=%s",
                endpoint,
                previous_owner_id,
                owner_id,
            )
            existing.owner_id = owner_id
        existing.p256dh = p256dh
        existing.auth = auth
        existing.user_agent = user_agent
        existing.last_seen_at = datetime.now(UTC)
        existing.revoked_at = None
        session.flush()
        return existing

    sub = PushSubscription(
        id=sub_id,
        owner_id=owner_id,
        endpoint=endpoint,
        p256dh=p256dh,
        auth=auth,
        user_agent=user_agent,
        last_seen_at=datetime.now(UTC),
    )
    session.add(sub)
    session.flush()
    return sub


def list_active_subscriptions(session: Session, owner_id: str) -> list[PushSubscription]:
    return list(
        session.scalars(
            select(PushSubscription).where(
                PushSubscription.owner_id == owner_id,
                PushSubscription.revoked_at.is_(None),
            )
        )
    )


def revoke_subscription_by_endpoint(session: Session, owner_id: str, endpoint: str) -> bool:
    sub = session.scalar(
        select(PushSubscription).where(
            PushSubscription.owner_id == owner_id,
            PushSubscription.endpoint == endpoint,
            PushSubscription.revoked_at.is_(None),
        )
    )
    if sub is None:
        return False
    sub.revoked_at = datetime.now(UTC)
    session.flush()
    return True


def mark_revoked(session: Session, subscription: PushSubscription) -> None:
    subscription.revoked_at = datetime.now(UTC)
    session.flush()


def delete_revoked_before(session: Session, cutoff: datetime) -> int:
    result = session.execute(
        delete(PushSubscription).where(
            PushSubscription.revoked_at.is_not(None),
            PushSubscription.revoked_at < cutoff,
        )
    )
    return result.rowcount or 0
