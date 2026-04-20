"""add check-in action tokens table

Revision ID: 0011_check_in_action_tokens
Revises: 0010_push_subscriptions
Create Date: 2026-04-19 14:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0011_check_in_action_tokens"
down_revision = "0010_push_subscriptions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "check_in_action_tokens",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "owner_id",
            sa.String(length=64),
            sa.ForeignKey("owners.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "cycle_scheduled_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("owner_id", "cycle_scheduled_at", name="uq_check_in_token_cycle"),
    )
    op.create_index(
        "ix_check_in_token_hash",
        "check_in_action_tokens",
        ["token_hash"],
    )


def downgrade() -> None:
    op.drop_index("ix_check_in_token_hash", table_name="check_in_action_tokens")
    op.drop_table("check_in_action_tokens")
