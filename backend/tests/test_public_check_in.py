"""Tests for public check-in action token flow."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.db.models import CheckInActionToken, CheckInEvent
from app.repositories.check_in import get_check_in_config
from app.services.check_in import acknowledge_check_in
from app.services.check_in_action_token import (
    _hash_token,
    generate_action_token,
    is_token_expired,
    lookup_token,
    mark_token_used,
)


def _make_config(session, owner_id: str, **overrides):
    """Get or create a check-in config for testing."""
    from app.db.models import CheckInConfig

    config = get_check_in_config(session, owner_id)
    if config is not None:
        for key, value in overrides.items():
            setattr(config, key, value)
        session.flush()
        return config

    config = CheckInConfig(
        owner_id=owner_id,
        interval_hours=overrides.get("interval_hours", 6),
        escalation_delay_minutes=overrides.get("escalation_delay_minutes", 30),
        push_enabled=overrides.get("push_enabled", True),
        email_enabled=overrides.get("email_enabled", True),
        next_scheduled_at=overrides.get(
            "next_scheduled_at", datetime.now(UTC) + timedelta(hours=6)
        ),
    )
    session.add(config)
    session.flush()
    return config


class TestTokenHashing:
    def test_hash_token_deterministic(self):
        raw = "abc123"
        assert _hash_token(raw) == _hash_token(raw)

    def test_hash_token_different_inputs(self):
        assert _hash_token("a") != _hash_token("b")


class TestTokenGeneration:
    def test_generates_raw_token(self, test_database_url, client, auth_headers):
        """generate_action_token returns a URL-safe string."""
        # Get the demo owner's config via the API
        resp = client.get("/check-in-config", headers=auth_headers)
        assert resp.status_code == 200

        # Access DB directly to test the service
        from app.db.session import get_session_factory

        session = get_session_factory()()
        try:
            config = get_check_in_config(session, "owner-demo")
            assert config is not None
            raw = generate_action_token(session, config)
            assert isinstance(raw, str)
            assert len(raw) > 10
            session.rollback()
        finally:
            session.close()

    def test_token_stored_as_hash(self, test_database_url, client, auth_headers):
        """Token hash is stored in DB, not the raw token."""
        from app.db.session import get_session_factory

        session = get_session_factory()()
        try:
            config = _make_config(session, "owner-demo")
            raw = generate_action_token(session, config)

            tokens = list(
                session.scalars(
                    select(CheckInActionToken).where(CheckInActionToken.owner_id == "owner-demo")
                ).all()
            )
            assert len(tokens) >= 1
            stored = tokens[-1]
            assert stored.token_hash == _hash_token(raw)
            assert stored.token_hash != raw
            session.rollback()
        finally:
            session.close()

    def test_same_cycle_returns_new_raw(self, test_database_url):
        """Calling generate_action_token twice for the same cycle regenerates the token."""
        from app.db.session import get_session_factory

        session = get_session_factory()()
        try:
            config = _make_config(session, "owner-demo")
            raw1 = generate_action_token(session, config)
            raw2 = generate_action_token(session, config)
            # Both should be valid tokens but different raw values (hash rotated)
            assert raw1 != raw2
            session.rollback()
        finally:
            session.close()


class TestTokenLookup:
    def test_lookup_finds_valid_token(self, test_database_url):
        from app.db.session import get_session_factory

        session = get_session_factory()()
        try:
            config = _make_config(session, "owner-demo")
            raw = generate_action_token(session, config)

            found = lookup_token(session, raw)
            assert found is not None
            assert found.owner_id == "owner-demo"
            session.rollback()
        finally:
            session.close()

    def test_lookup_returns_none_for_invalid(self, test_database_url):
        from app.db.session import get_session_factory

        session = get_session_factory()()
        try:
            found = lookup_token(session, "nonexistent-token-value")
            assert found is None
            session.rollback()
        finally:
            session.close()


class TestTokenExpiry:
    def test_not_expired_when_future(self, test_database_url):
        from app.db.session import get_session_factory

        session = get_session_factory()()
        try:
            config = _make_config(
                session,
                "owner-demo",
                next_scheduled_at=datetime.now(UTC) + timedelta(hours=6),
            )
            raw = generate_action_token(session, config)
            token = lookup_token(session, raw)
            assert token is not None
            assert not is_token_expired(token)
            session.rollback()
        finally:
            session.close()

    def test_expired_when_past(self, test_database_url):
        from app.db.session import get_session_factory

        session = get_session_factory()()
        try:
            # Create token with cycle_scheduled_at in the past so expires_at is in the past
            config = _make_config(
                session,
                "owner-demo",
                next_scheduled_at=datetime.now(UTC) - timedelta(hours=25),
            )
            raw = generate_action_token(session, config)
            token = lookup_token(session, raw)
            assert token is not None
            assert is_token_expired(token)
            session.rollback()
        finally:
            session.close()


class TestTokenUsage:
    def test_mark_used_sets_timestamp(self, test_database_url):
        from app.db.session import get_session_factory

        session = get_session_factory()()
        try:
            config = _make_config(session, "owner-demo")
            raw = generate_action_token(session, config)
            token = lookup_token(session, raw)
            assert token is not None
            assert token.used_at is None

            mark_token_used(token)
            assert token.used_at is not None
            session.rollback()
        finally:
            session.close()


class TestAcknowledgeWithMethod:
    def test_acknowledge_with_public_link_method(self, test_database_url):
        """acknowledge_check_in stores the provided method."""
        from app.db.session import get_session_factory

        session = get_session_factory()()
        try:
            _make_config(
                session,
                "owner-demo",
                next_scheduled_at=datetime.now(UTC) - timedelta(minutes=5),
            )
            session.commit()

            result = acknowledge_check_in(session, "owner-demo", method="public_link")
            session.commit()

            assert result.mode == "normal"

            events = list(
                session.scalars(
                    select(CheckInEvent).where(
                        CheckInEvent.owner_id == "owner-demo",
                        CheckInEvent.status == "acknowledged",
                    )
                ).all()
            )
            assert len(events) >= 1
            assert events[-1].method == "public_link"
        finally:
            session.close()

    def test_acknowledge_default_method_is_webapp(self, test_database_url):
        """acknowledge_check_in defaults to 'webapp' method."""
        from app.db.session import get_session_factory

        session = get_session_factory()()
        try:
            _make_config(
                session,
                "owner-demo",
                next_scheduled_at=datetime.now(UTC) - timedelta(minutes=5),
            )
            session.commit()

            acknowledge_check_in(session, "owner-demo")
            session.commit()

            events = list(
                session.scalars(
                    select(CheckInEvent).where(
                        CheckInEvent.owner_id == "owner-demo",
                        CheckInEvent.status == "acknowledged",
                    )
                ).all()
            )
            assert len(events) >= 1
            assert events[-1].method == "webapp"
        finally:
            session.close()
