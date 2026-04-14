"""add escalation events table

Revision ID: 0003_escalation
Revises: 0002_auth
Create Date: 2026-04-15 16:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0003_escalation"
down_revision = "0002_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "escalation_events",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "owner_id",
            sa.String(length=64),
            sa.ForeignKey("owners.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "resolved_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("escalation_events")
