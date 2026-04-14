from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class CheckInMethod(StrEnum):
    PUSH = "push"
    EMAIL = "email"
    WEBAPP = "webapp"


class CheckInStatus(StrEnum):
    ACKNOWLEDGED = "acknowledged"
    MISSED = "missed"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
    )


class Owner(Base):
    __tablename__ = "owners"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    pets: Mapped[list[Pet]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    emergency_contacts: Mapped[list[EmergencyContact]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    check_in_config: Mapped[CheckInConfig | None] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    check_in_events: Mapped[list[CheckInEvent]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )


class Pet(TimestampMixin, Base):
    __tablename__ = "pets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("owners.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    breed: Mapped[str] = mapped_column(String(255), nullable=False)
    age_years: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    chip_number: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    pre_existing_conditions: Mapped[str] = mapped_column(Text, nullable=False)
    allergies: Mapped[str] = mapped_column(Text, nullable=False)
    medications: Mapped[str] = mapped_column(Text, nullable=False)
    vaccination_status: Mapped[str] = mapped_column(Text, nullable=False)
    insurance: Mapped[str] = mapped_column(Text, nullable=False)
    veterinarian_name: Mapped[str] = mapped_column(String(255), nullable=False)
    veterinarian_phone: Mapped[str] = mapped_column(String(255), nullable=False)
    feeding_notes: Mapped[str] = mapped_column(Text, nullable=False)
    special_needs: Mapped[str] = mapped_column(Text, nullable=False)
    spare_key_location: Mapped[str] = mapped_column(Text, nullable=False)
    emergency_access_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True
    )

    owner: Mapped[Owner] = relationship(back_populates="pets")


class EmergencyContact(TimestampMixin, Base):
    __tablename__ = "emergency_contacts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("owners.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    relationship_label: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    has_apartment_key: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_take_dog: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)

    owner: Mapped[Owner] = relationship(back_populates="emergency_contacts")
    chain_entry: Mapped[EmergencyChainEntry | None] = relationship(
        back_populates="contact",
        cascade="all, delete-orphan",
        uselist=False,
    )


class EmergencyChainEntry(Base):
    __tablename__ = "emergency_chain_entries"
    __table_args__ = (
        UniqueConstraint("owner_id", "contact_id", name="uq_emergency_chain_contact"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("owners.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[str] = mapped_column(
        ForeignKey("emergency_contacts.id", ondelete="CASCADE"),
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False)

    contact: Mapped[EmergencyContact] = relationship(back_populates="chain_entry")


class CheckInConfig(Base):
    __tablename__ = "check_in_configs"

    owner_id: Mapped[str] = mapped_column(
        ForeignKey("owners.id", ondelete="CASCADE"),
        primary_key=True,
    )
    interval_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    escalation_delay_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    primary_method: Mapped[str] = mapped_column(String(32), nullable=False)
    backup_method: Mapped[str] = mapped_column(String(32), nullable=False)
    next_scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    owner: Mapped[Owner] = relationship(back_populates="check_in_config")


class CheckInEvent(TimestampMixin, Base):
    __tablename__ = "check_in_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("owners.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False)

    owner: Mapped[Owner] = relationship(back_populates="check_in_events")
