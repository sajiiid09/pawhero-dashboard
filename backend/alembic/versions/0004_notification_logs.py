"""add notification logs table

Revision ID: 0004_notification_logs
Revises: 0003_escalation
Create Date: 2026-04-15 18:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0004_notification_logs"
down_revision = "0003_escalation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_logs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "owner_id",
            sa.String(length=64),
            sa.ForeignKey("owners.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "escalation_event_id",
            sa.String(length=64),
            sa.ForeignKey("escalation_events.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("recipient_email", sa.String(length=255), nullable=False),
        sa.Column("notification_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("notification_logs")
