from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CheckInActionToken


def find_token_by_hash(session: Session, token_hash: str) -> CheckInActionToken | None:
    return session.scalar(
        select(CheckInActionToken).where(CheckInActionToken.token_hash == token_hash)
    )


def find_token_for_cycle(
    session: Session,
    owner_id: str,
    cycle_scheduled_at: datetime,
) -> CheckInActionToken | None:
    return session.scalar(
        select(CheckInActionToken).where(
            CheckInActionToken.owner_id == owner_id,
            CheckInActionToken.cycle_scheduled_at == cycle_scheduled_at,
        )
    )


def create_action_token(
    session: Session,
    *,
    token_id: str,
    owner_id: str,
    cycle_scheduled_at: datetime,
    token_hash: str,
    expires_at: datetime,
) -> CheckInActionToken:
    token = CheckInActionToken(
        id=token_id,
        owner_id=owner_id,
        cycle_scheduled_at=cycle_scheduled_at,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    session.add(token)
    session.flush()
    return token


def mark_token_used(token: CheckInActionToken, used_at: datetime) -> None:
    token.used_at = used_at
    _session_flush(token)


def _session_flush(obj: object) -> None:
    from sqlalchemy import inspect

    session = inspect(obj).session
    if session is not None:
        session.flush()
