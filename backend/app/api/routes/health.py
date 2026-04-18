from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.db.session import get_session_factory

router = APIRouter(tags=["health"])


@router.get("/health")
def healthcheck():
    session = get_session_factory()()
    try:
        session.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database_unavailable",
        ) from exc
    finally:
        session.close()

    return {"status": "ok", "database": "ok"}
