"""add contact push subscriptions table

Revision ID: 0012_contact_push_subscriptions
Revises: 0011_check_in_action_tokens
Create Date: 2026-04-19 16:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0012_contact_push_subscriptions"
down_revision = "0011_check_in_action_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contact_push_subscriptions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
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
        sa.UniqueConstraint("endpoint", name="uq_contact_push_endpoint"),
    )
    op.create_index(
        "ix_contact_push_email_active",
        "contact_push_subscriptions",
        ["email", "revoked_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_contact_push_email_active", table_name="contact_push_subscriptions")
    op.drop_table("contact_push_subscriptions")
