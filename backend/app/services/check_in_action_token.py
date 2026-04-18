from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models import CheckInActionToken, CheckInConfig
from app.repositories import check_in_action_token as token_repo
from app.services.auth import generate_id

TOKEN_EXPIRY_HOURS = 24


def generate_action_token(
    session: Session,
    config: CheckInConfig,
) -> str:
    """Generate (or return existing) action token for the current check-in cycle.

    Returns the raw token string (URL-safe). The SHA-256 hash is stored in the DB.
    """
    cycle_scheduled_at = config.next_scheduled_at
    if cycle_scheduled_at.tzinfo is None:
        cycle_scheduled_at = cycle_scheduled_at.replace(tzinfo=UTC)

    existing = token_repo.find_token_for_cycle(session, config.owner_id, cycle_scheduled_at)
    if existing is not None:
        # Token already generated for this cycle — cannot return raw token.
        # Generate a fresh one by updating the hash.
        raw_token = secrets.token_urlsafe(32)
        existing.token_hash = _hash_token(raw_token)
        existing.expires_at = cycle_scheduled_at + timedelta(hours=TOKEN_EXPIRY_HOURS)
        session.flush()
        return raw_token

    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    expires_at = cycle_scheduled_at + timedelta(hours=TOKEN_EXPIRY_HOURS)

    token_repo.create_action_token(
        session,
        token_id=generate_id(),
        owner_id=config.owner_id,
        cycle_scheduled_at=cycle_scheduled_at,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    return raw_token


def lookup_token(session: Session, raw_token: str) -> CheckInActionToken | None:
    """Look up an action token by its raw value. Returns None if not found."""
    token_hash = _hash_token(raw_token)
    return token_repo.find_token_by_hash(session, token_hash)


def is_token_expired(token: CheckInActionToken) -> bool:
    """Check if the token has passed its expiry time."""
    now = datetime.now(UTC)
    expires_at = token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return now >= expires_at


def mark_token_used(token: CheckInActionToken) -> None:
    """Mark the token as used at the current time."""
    token_repo.mark_token_used(token, datetime.now(UTC))


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()
