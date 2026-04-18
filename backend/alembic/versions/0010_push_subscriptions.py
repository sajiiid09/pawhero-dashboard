"""add push subscriptions table

Revision ID: 0010_push_subscriptions
Revises: 0009_notification_prefs
Create Date: 2026-04-19 12:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0010_push_subscriptions"
down_revision = "0009_notification_prefs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "owner_id",
            sa.String(length=64),
            sa.ForeignKey("owners.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("p256dh", sa.String(length=255), nullable=False),
        sa.Column("auth", sa.String(length=255), nullable=False),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("endpoint", name="uq_push_sub_endpoint"),
    )
    op.create_index(
        "ix_push_sub_owner_active",
        "push_subscriptions",
        ["owner_id", "revoked_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_push_sub_owner_active", table_name="push_subscriptions")
    op.drop_table("push_subscriptions")
