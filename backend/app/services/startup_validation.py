from __future__ import annotations

import logging
from urllib.parse import urlparse

from app.core.config import Settings

logger = logging.getLogger(__name__)

PLACEHOLDER_JWT_SECRET = "change-me-in-production-with-32-byte-minimum"


def validate_startup_settings(settings: Settings) -> None:
    errors = _collect_startup_errors(settings)
    if not errors:
        return

    message = "Invalid production configuration: " + "; ".join(errors)
    if settings.app_env.lower() == "production":
        raise RuntimeError(message)

    logger.warning(message)


def _collect_startup_errors(settings: Settings) -> list[str]:
    errors: list[str] = []

    if not settings.database_url.strip():
        errors.append("DATABASE_URL is required")

    parsed_database_url = urlparse(settings.database_url)
    if parsed_database_url.port == 6543 and settings.db_pool_mode != "transaction":
        errors.append(
            "DATABASE_URL uses Supabase transaction pooler port 6543; "
            "set DB_POOL_MODE=transaction"
        )

    if settings.jwt_secret_key == PLACEHOLDER_JWT_SECRET:
        errors.append("JWT_SECRET_KEY must be changed from the placeholder")

    if not settings.supabase_url.strip():
        errors.append("SUPABASE_URL is required for storage")
    if not settings.supabase_secret_key.strip():
        errors.append("SUPABASE_SECRET_KEY is required for backend storage access")
    if not settings.supabase_publishable_key.strip():
        errors.append("SUPABASE_PUBLISHABLE_KEY is required for Supabase project configuration")

    if not settings.vapid_public_key.strip():
        errors.append("VAPID_PUBLIC_KEY is required for web push")
    if not settings.vapid_private_key.strip():
        errors.append("VAPID_PRIVATE_KEY is required for web push")
    if not settings.vapid_subject.strip():
        errors.append("VAPID_SUBJECT is required for web push")

    return errors
