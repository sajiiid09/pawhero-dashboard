from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.services.maintenance import cleanup_expired_records
from app.services.notification_dispatcher import dispatch_notifications

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def start_scheduler() -> None:
    global _scheduler

    settings = get_settings()
    if not settings.scheduler_enabled:
        logger.info("notification scheduler disabled by SCHEDULER_ENABLED=false")
        return

    if _scheduler is not None and _scheduler.running:
        logger.info("notification scheduler already running")
        return

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(_dispatch_job, "interval", seconds=60, id="dispatch_notifications")
    _scheduler.add_job(_maintenance_job, "interval", hours=24, id="maintenance_cleanup")
    _scheduler.start()
    logger.info("notification scheduler started (interval=60s)")


def shutdown_scheduler() -> None:
    global _scheduler

    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        logger.info("notification scheduler stopped")
        _scheduler = None


def _dispatch_job() -> None:
    session = get_session_factory()()
    try:
        dispatch_notifications(session)
    except Exception:
        logger.exception("notification dispatch job failed")
    finally:
        session.close()


def _maintenance_job() -> None:
    session = get_session_factory()()
    try:
        result = cleanup_expired_records(session)
        session.commit()
        logger.info(
            "maintenance cleanup completed "
            "expired_check_in_tokens=%d revoked_push_subscriptions=%d",
            result.expired_check_in_tokens,
            result.revoked_push_subscriptions,
        )
    except Exception:
        session.rollback()
        logger.exception("maintenance cleanup job failed")
    finally:
        session.close()
