from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db_session

DbSession = Annotated[Session, Depends(get_db_session)]


def get_demo_owner_id() -> str:
    settings = get_settings()
    if not settings.demo_owner_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Demo owner is not configured.",
        )
    return settings.demo_owner_id


OwnerId = Annotated[str, Depends(get_demo_owner_id)]
