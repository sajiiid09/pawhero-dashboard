from __future__ import annotations

from datetime import datetime
from enum import StrEnum

import sqlalchemy as sa
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class CheckInMethod(StrEnum):
    PUSH = "push"
    EMAIL = "email"
    WEBAPP = "webapp"
    PUBLIC_LINK = "public_link"


class NotificationChannel(StrEnum):
    PUSH = "push"
    EMAIL = "email"


class NotificationType(StrEnum):
    OWNER_REMINDER = "owner_reminder"
    OWNER_ESCALATION = "owner_escalation"
    EMERGENCY_CONTACT_ESCALATION = "emergency_contact_escalation"
    RESPONDER_ACKNOWLEDGMENT = "responder_acknowledgment"


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
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_verification_code_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email_verification_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    email_verification_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

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
    escalation_events: Mapped[list[EscalationEvent]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    notification_logs: Mapped[list[NotificationLog]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    pet_documents: Mapped[list[PetDocument]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    push_subscriptions: Mapped[list[PushSubscription]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    check_in_action_tokens: Mapped[list[CheckInActionToken]] = relationship(
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
    documents: Mapped[list[PetDocument]] = relationship(
        back_populates="pet", cascade="all, delete-orphan"
    )


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
    __table_args__ = (
        sa.CheckConstraint(
            "push_enabled = TRUE OR email_enabled = TRUE",
            name="ck_check_in_configs_at_least_one_channel",
        ),
    )

    owner_id: Mapped[str] = mapped_column(
        ForeignKey("owners.id", ondelete="CASCADE"),
        primary_key=True,
    )
    interval_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    escalation_delay_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
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


class EscalationEvent(TimestampMixin, Base):
    __tablename__ = "escalation_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("owners.id", ondelete="CASCADE"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped[Owner] = relationship(back_populates="escalation_events")
    acknowledgments: Mapped[list[ResponderAcknowledgment]] = relationship(
        back_populates="escalation_event",
        cascade="all, delete-orphan",
    )


class NotificationLog(TimestampMixin, Base):
    __tablename__ = "notification_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("owners.id", ondelete="CASCADE"), nullable=False
    )
    escalation_event_id: Mapped[str | None] = mapped_column(
        ForeignKey("escalation_events.id", ondelete="SET NULL"), nullable=True
    )
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    notification_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner: Mapped[Owner] = relationship(back_populates="notification_logs")


class ResponderAcknowledgment(TimestampMixin, Base):
    __tablename__ = "responder_acknowledgments"
    __table_args__ = (
        UniqueConstraint("escalation_event_id", "responder_email", name="uq_responder_ack"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    escalation_event_id: Mapped[str] = mapped_column(
        ForeignKey("escalation_events.id", ondelete="CASCADE"), nullable=False
    )
    pet_id: Mapped[str] = mapped_column(ForeignKey("pets.id", ondelete="CASCADE"), nullable=False)
    responder_email: Mapped[str] = mapped_column(String(255), nullable=False)
    responder_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    escalation_event: Mapped[EscalationEvent] = relationship(back_populates="acknowledgments")


class PetDocument(TimestampMixin, Base):
    __tablename__ = "pet_documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("owners.id", ondelete="CASCADE"), nullable=False
    )
    pet_id: Mapped[str] = mapped_column(ForeignKey("pets.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(32), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    owner: Mapped[Owner] = relationship(back_populates="pet_documents")
    pet: Mapped[Pet] = relationship(back_populates="documents")


class CheckInActionToken(TimestampMixin, Base):
    __tablename__ = "check_in_action_tokens"
    __table_args__ = (
        UniqueConstraint("owner_id", "cycle_scheduled_at", name="uq_check_in_token_cycle"),
        Index("ix_check_in_token_hash", "token_hash"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("owners.id", ondelete="CASCADE"), nullable=False
    )
    cycle_scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped[Owner] = relationship(back_populates="check_in_action_tokens")


class PushSubscription(TimestampMixin, Base):
    __tablename__ = "push_subscriptions"
    __table_args__ = (
        UniqueConstraint("endpoint", name="uq_push_sub_endpoint"),
        Index("ix_push_sub_owner_active", "owner_id", "revoked_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("owners.id", ondelete="CASCADE"), nullable=False
    )
    endpoint: Mapped[str] = mapped_column(Text, nullable=False)
    p256dh: Mapped[str] = mapped_column(String(255), nullable=False)
    auth: Mapped[str] = mapped_column(String(255), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped[Owner] = relationship(back_populates="push_subscriptions")
