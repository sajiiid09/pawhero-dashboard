from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.repositories import check_in_action_token as token_repo
from app.repositories import push as push_repo


@dataclass(frozen=True)
class MaintenanceCleanupResult:
    expired_check_in_tokens: int
    revoked_push_subscriptions: int


def cleanup_expired_records(
    session: Session,
    now: datetime | None = None,
) -> MaintenanceCleanupResult:
    settings = get_settings()
    current_time = now or datetime.now(UTC)
    token_cutoff = current_time - timedelta(days=settings.check_in_token_retention_days)
    push_cutoff = current_time - timedelta(days=settings.revoked_push_retention_days)

    expired_tokens = token_repo.delete_expired_before(session, token_cutoff)
    revoked_push_subscriptions = push_repo.delete_revoked_before(session, push_cutoff)

    return MaintenanceCleanupResult(
        expired_check_in_tokens=expired_tokens,
        revoked_push_subscriptions=revoked_push_subscriptions,
    )
