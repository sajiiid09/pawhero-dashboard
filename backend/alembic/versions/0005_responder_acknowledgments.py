"""add responder acknowledgments table

Revision ID: 0005_responder_acknowledgments
Revises: 0004_notification_logs
Create Date: 2026-04-15 20:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0005_responder_acknowledgments"
down_revision = "0004_notification_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "responder_acknowledgments",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "escalation_event_id",
            sa.String(length=64),
            sa.ForeignKey("escalation_events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "pet_id",
            sa.String(length=64),
            sa.ForeignKey("pets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("responder_email", sa.String(length=255), nullable=False),
        sa.Column("responder_name", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("escalation_event_id", "responder_email", name="uq_responder_ack"),
    )


def downgrade() -> None:
    op.drop_table("responder_acknowledgments")
