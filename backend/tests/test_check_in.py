from datetime import UTC, datetime, timedelta

from app.services.check_in import EscalationMode, compute_escalation_state


class _Config:
    def __init__(self, next_at: datetime, delay: int = 30):
        self.next_scheduled_at = next_at
        self.escalation_delay_minutes = delay


def test_normal_when_not_yet_due():
    future = datetime.now(UTC) + timedelta(hours=1)
    mode, deadline = compute_escalation_state(_Config(future))
    assert mode == EscalationMode.NORMAL
    assert deadline is None


def test_pending_when_overdue_but_within_grace():
    past = datetime.now(UTC) - timedelta(minutes=5)
    mode, deadline = compute_escalation_state(_Config(past, delay=30))
    assert mode == EscalationMode.PENDING
    assert deadline is not None


def test_escalated_after_grace_period():
    past = datetime.now(UTC) - timedelta(minutes=60)
    mode, deadline = compute_escalation_state(_Config(past, delay=30))
    assert mode == EscalationMode.ESCALATED
    assert deadline is not None


def test_normal_when_no_config():
    mode, deadline = compute_escalation_state(None)
    assert mode == EscalationMode.NORMAL
    assert deadline is None
