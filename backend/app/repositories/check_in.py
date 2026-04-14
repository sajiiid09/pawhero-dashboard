from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from app.db.models import CheckInConfig, CheckInEvent


def get_check_in_config(session: Session, owner_id: str) -> CheckInConfig | None:
    statement = select(CheckInConfig).where(CheckInConfig.owner_id == owner_id)
    return session.scalar(statement)


def list_recent_check_in_events(session: Session, owner_id: str, limit: int = 3) -> list[CheckInEvent]:
    statement: Select[tuple[CheckInEvent]] = (
        select(CheckInEvent)
        .where(CheckInEvent.owner_id == owner_id)
        .order_by(desc(CheckInEvent.acknowledged_at))
        .limit(limit)
    )
    return list(session.scalars(statement))
