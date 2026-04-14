from pydantic import Field

from app.schemas.common import AppSchema


class EmergencyContactDTO(AppSchema):
    id: str
    name: str
    relationship: str
    phone: str
    email: str
    has_apartment_key: bool = Field(alias="hasApartmentKey")
    can_take_dog: bool = Field(alias="canTakeDog")
    notes: str


class EmergencyChainContactDTO(EmergencyContactDTO):
    priority: int


class EmergencyContactUpsertRequest(AppSchema):
    name: str
    relationship: str
    phone: str
    email: str
    priority: int
    has_apartment_key: bool = Field(alias="hasApartmentKey")
    can_take_dog: bool = Field(alias="canTakeDog")
    notes: str


class MoveEmergencyContactRequest(AppSchema):
    direction: str
