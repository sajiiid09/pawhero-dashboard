from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.pool import NullPool

from app.api.routes import health
from app.core.config import Settings
from app.db.models import CheckInActionToken, PushSubscription
from app.db.session import build_engine_kwargs, get_session_factory, reset_database_state
from app.services.maintenance import cleanup_expired_records
from app.services.startup_validation import validate_startup_settings


def _settings(**overrides) -> Settings:
    defaults = {
        "DATABASE_URL": "postgresql+psycopg://postgres:postgres@localhost:5432/pawhero",
        "JWT_SECRET_KEY": "x" * 32,
        "SUPABASE_URL": "https://project.supabase.co",
        "SUPABASE_SECRET_KEY": "sb_secret_placeholder",
        "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_placeholder",
    }
    defaults.update(overrides)
    return Settings(**defaults)


def test_transaction_pooler_engine_uses_null_pool_and_disables_prepared_statements():
    settings = _settings(
        DATABASE_URL=(
            "postgresql+psycopg://postgres.ref:pass@aws-0-eu.pooler.supabase.com:6543/postgres"
        ),
        DB_POOL_MODE="transaction",
    )

    kwargs = build_engine_kwargs(settings)

    assert kwargs["poolclass"] is NullPool
    assert kwargs["connect_args"]["prepare_threshold"] is None
    assert kwargs["connect_args"]["connect_timeout"] == 10
    assert kwargs["connect_args"]["options"] == "-c statement_timeout=30000"
    assert "pool_pre_ping" not in kwargs


def test_session_pool_engine_keeps_pre_ping_without_disabling_prepared_statements():
    settings = _settings(DB_POOL_MODE="session")

    kwargs = build_engine_kwargs(settings)

    assert kwargs["pool_pre_ping"] is True
    assert "poolclass" not in kwargs
    assert "prepare_threshold" not in kwargs["connect_args"]


def test_production_startup_validation_fails_for_placeholders():
    settings = _settings(
        APP_ENV="production",
        JWT_SECRET_KEY="change-me-in-production-with-32-byte-minimum",
        SUPABASE_SECRET_KEY="",
    )

    with pytest.raises(RuntimeError) as exc_info:
        validate_startup_settings(settings)

    message = str(exc_info.value)
    assert "JWT_SECRET_KEY" in message
    assert "SUPABASE_SECRET_KEY" in message


def test_scheduler_does_not_start_when_disabled(monkeypatch):
    from app.services import scheduler

    scheduler.shutdown_scheduler()
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")
    reset_database_state()

    scheduler.start_scheduler()

    assert scheduler._scheduler is None

    monkeypatch.delenv("SCHEDULER_ENABLED", raising=False)
    reset_database_state()


def test_cleanup_expired_records_prunes_only_old_records(test_database_url):
    del test_database_url

    session = get_session_factory()()
    now = datetime.now(UTC)
    old_token = CheckInActionToken(
        id=f"token-old-{uuid4().hex}",
        owner_id="owner-demo",
        cycle_scheduled_at=now - timedelta(days=11),
        token_hash="a" * 64,
        expires_at=now - timedelta(days=8),
    )
    fresh_token = CheckInActionToken(
        id=f"token-new-{uuid4().hex}",
        owner_id="owner-demo",
        cycle_scheduled_at=now - timedelta(days=2),
        token_hash="b" * 64,
        expires_at=now - timedelta(days=1),
    )
    old_push = PushSubscription(
        id=f"push-old-{uuid4().hex}",
        owner_id="owner-demo",
        endpoint=f"https://push.example.com/{uuid4().hex}",
        p256dh="key",
        auth="auth",
        user_agent="Test",
        last_seen_at=now - timedelta(days=40),
        revoked_at=now - timedelta(days=31),
    )
    fresh_push = PushSubscription(
        id=f"push-new-{uuid4().hex}",
        owner_id="owner-demo",
        endpoint=f"https://push.example.com/{uuid4().hex}",
        p256dh="key",
        auth="auth",
        user_agent="Test",
        last_seen_at=now - timedelta(days=3),
        revoked_at=now - timedelta(days=3),
    )
    session.add_all([old_token, fresh_token, old_push, fresh_push])
    session.flush()

    try:
        result = cleanup_expired_records(session, now=now)

        assert result.expired_check_in_tokens == 1
        assert result.revoked_push_subscriptions == 1
        assert session.get(CheckInActionToken, old_token.id) is None
        assert session.get(PushSubscription, old_push.id) is None
        assert session.scalar(
            select(CheckInActionToken).where(CheckInActionToken.id == fresh_token.id)
        )
        assert session.scalar(select(PushSubscription).where(PushSubscription.id == fresh_push.id))
    finally:
        session.rollback()
        session.close()


def test_healthcheck_fails_cleanly_when_database_is_unavailable(monkeypatch):
    class BrokenSession:
        def execute(self, _statement):
            raise RuntimeError("database down")

        def close(self):
            pass

    monkeypatch.setattr(health, "get_session_factory", lambda: BrokenSession)

    with pytest.raises(HTTPException) as exc_info:
        health.healthcheck()

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "database_unavailable"
