from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ResponderAcknowledgment


def create_acknowledgment(
    session: Session,
    ack_id: str,
    escalation_event_id: str,
    pet_id: str,
    responder_email: str,
    responder_name: str | None = None,
) -> ResponderAcknowledgment:
    ack = ResponderAcknowledgment(
        id=ack_id,
        escalation_event_id=escalation_event_id,
        pet_id=pet_id,
        responder_email=responder_email,
        responder_name=responder_name,
    )
    session.add(ack)
    session.flush()
    return ack


def has_acknowledged(
    session: Session,
    escalation_event_id: str,
    responder_email: str,
) -> bool:
    row = session.scalar(
        select(ResponderAcknowledgment).where(
            ResponderAcknowledgment.escalation_event_id == escalation_event_id,
            ResponderAcknowledgment.responder_email == responder_email,
        )
    )
    return row is not None


def count_acknowledgments(
    session: Session,
    escalation_event_id: str,
) -> int:
    from sqlalchemy import func

    result = session.scalar(
        select(func.count())
        .select_from(ResponderAcknowledgment)
        .where(
            ResponderAcknowledgment.escalation_event_id == escalation_event_id,
        )
    )
    return result or 0
