from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import get_session_factory
from app.services.notification_dispatcher import dispatch_notifications

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def start_scheduler() -> None:
    global _scheduler

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(_dispatch_job, "interval", seconds=60, id="dispatch_notifications")
    _scheduler.start()
    logger.info("notification scheduler started (interval=60s)")


def shutdown_scheduler() -> None:
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        logger.info("notification scheduler stopped")


def _dispatch_job() -> None:
    session = get_session_factory()()
    try:
        dispatch_notifications(session)
    except Exception:
        logger.exception("notification dispatch job failed")
    finally:
        session.close()
