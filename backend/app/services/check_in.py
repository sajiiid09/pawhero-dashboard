from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models import CheckInConfig
from app.repositories.check_in import get_check_in_config
from app.schemas.check_in import CheckInConfigDTO, CheckInConfigUpdateRequest


def recompute_next_scheduled_at(interval_hours: int) -> datetime:
    return datetime.now(UTC) + timedelta(hours=interval_hours)


def save_check_in_config(
    session: Session,
    owner_id: str,
    payload: CheckInConfigUpdateRequest,
) -> CheckInConfig:
    config = get_check_in_config(session, owner_id)

    if config is None:
        config = CheckInConfig(owner_id=owner_id)
        session.add(config)

    config.interval_hours = payload.interval_hours
    config.escalation_delay_minutes = payload.escalation_delay_minutes
    config.primary_method = payload.primary_method
    config.backup_method = payload.backup_method
    config.next_scheduled_at = recompute_next_scheduled_at(payload.interval_hours)

    session.flush()
    session.refresh(config)
    return config


def serialize_check_in_config(config: CheckInConfig) -> CheckInConfigDTO:
    return CheckInConfigDTO.model_validate(
        {
            "interval_hours": config.interval_hours,
            "escalation_delay_minutes": config.escalation_delay_minutes,
            "primary_method": config.primary_method,
            "backup_method": config.backup_method,
            "next_scheduled_at": config.next_scheduled_at.isoformat(),
        }
    )
