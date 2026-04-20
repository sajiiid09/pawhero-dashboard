"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-04-15 03:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "owners",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=255), nullable=False),
    )
    op.create_table(
        "pets",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "owner_id",
            sa.String(length=64),
            sa.ForeignKey("owners.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("breed", sa.String(length=255), nullable=False),
        sa.Column("age_years", sa.Integer(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("chip_number", sa.String(length=255), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("pre_existing_conditions", sa.Text(), nullable=False),
        sa.Column("allergies", sa.Text(), nullable=False),
        sa.Column("medications", sa.Text(), nullable=False),
        sa.Column("vaccination_status", sa.Text(), nullable=False),
        sa.Column("insurance", sa.Text(), nullable=False),
        sa.Column("veterinarian_name", sa.String(length=255), nullable=False),
        sa.Column("veterinarian_phone", sa.String(length=255), nullable=False),
        sa.Column("feeding_notes", sa.Text(), nullable=False),
        sa.Column("special_needs", sa.Text(), nullable=False),
        sa.Column("spare_key_location", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_table(
        "emergency_contacts",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "owner_id",
            sa.String(length=64),
            sa.ForeignKey("owners.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("relationship_label", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("has_apartment_key", sa.Boolean(), nullable=False),
        sa.Column("can_take_dog", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_table(
        "emergency_chain_entries",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "owner_id",
            sa.String(length=64),
            sa.ForeignKey("owners.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "contact_id",
            sa.String(length=64),
            sa.ForeignKey("emergency_contacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.UniqueConstraint("owner_id", "contact_id", name="uq_emergency_chain_contact"),
    )
    op.create_table(
        "check_in_configs",
        sa.Column(
            "owner_id",
            sa.String(length=64),
            sa.ForeignKey("owners.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("interval_hours", sa.Integer(), nullable=False),
        sa.Column("escalation_delay_minutes", sa.Integer(), nullable=False),
        sa.Column("primary_method", sa.String(length=32), nullable=False),
        sa.Column("backup_method", sa.String(length=32), nullable=False),
        sa.Column("next_scheduled_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "check_in_events",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "owner_id",
            sa.String(length=64),
            sa.ForeignKey("owners.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("check_in_events")
    op.drop_table("check_in_configs")
    op.drop_table("emergency_chain_entries")
    op.drop_table("emergency_contacts")
    op.drop_table("pets")
    op.drop_table("owners")
