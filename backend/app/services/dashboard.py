from sqlalchemy.orm import Session

from app.repositories.check_in import get_check_in_config, list_recent_check_in_events
from app.repositories.emergency_chain import list_ordered_contacts
from app.repositories.pets import list_pets
from app.schemas.dashboard import (
    CheckInHistoryItemDTO,
    DashboardSummaryDTO,
    EscalationStatusDTO,
    MonitoredPetDTO,
)


def build_dashboard_summary(session: Session, owner_id: str) -> DashboardSummaryDTO:
    pets = list_pets(session, owner_id)
    contacts = list_ordered_contacts(session, owner_id)
    config = get_check_in_config(session, owner_id)
    check_in_events = list_recent_check_in_events(session, owner_id)

    primary_pet = pets[0] if pets else None

    return DashboardSummaryDTO.model_validate(
        {
            "pet_count": len(pets),
            "emergency_chain_status": "active" if len(contacts) >= 2 else "inactive",
            "next_check_in_at": config.next_scheduled_at.isoformat() if config else None,
            "recent_check_ins": [
                CheckInHistoryItemDTO(
                    id=event.id,
                    status=event.status,
                    acknowledged_at=event.acknowledged_at.isoformat(),
                    method=event.method,
                )
                for event in check_in_events
            ],
            "escalation_status": EscalationStatusDTO(
                mode="normal",
                title="Normalbetrieb",
                description="Alle Systeme laufen. Keine aktive Rettungskette.",
            ),
            "monitored_pet": MonitoredPetDTO(
                id=primary_pet.id,
                name=primary_pet.name,
                breed=primary_pet.breed,
                age_years=primary_pet.age_years,
                image_url=primary_pet.image_url,
            )
            if primary_pet
            else None,
        }
    )
