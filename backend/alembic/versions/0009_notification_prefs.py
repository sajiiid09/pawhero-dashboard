"""replace notification method columns with boolean toggles

Revision ID: 0009_notification_prefs
Revises: 0008_pet_documents
Create Date: 2026-04-19 10:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0009_notification_prefs"
down_revision = "0008_pet_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "check_in_configs",
        sa.Column("push_enabled", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "check_in_configs",
        sa.Column("email_enabled", sa.Boolean(), nullable=True),
    )

    # Migrate: every existing row had both push and email active.
    op.execute("UPDATE check_in_configs SET push_enabled = TRUE, email_enabled = TRUE")

    op.alter_column("check_in_configs", "push_enabled", nullable=False)
    op.alter_column("check_in_configs", "email_enabled", nullable=False)

    op.create_check_constraint(
        "ck_check_in_configs_at_least_one_channel",
        "check_in_configs",
        "push_enabled = TRUE OR email_enabled = TRUE",
    )

    op.drop_column("check_in_configs", "primary_method")
    op.drop_column("check_in_configs", "backup_method")


def downgrade() -> None:
    op.add_column(
        "check_in_configs",
        sa.Column("primary_method", sa.String(32), nullable=True),
    )
    op.add_column(
        "check_in_configs",
        sa.Column("backup_method", sa.String(32), nullable=True),
    )

    op.execute("UPDATE check_in_configs SET primary_method = 'push', backup_method = 'email'")

    op.alter_column("check_in_configs", "primary_method", nullable=False)
    op.alter_column("check_in_configs", "backup_method", nullable=False)

    op.drop_constraint(
        "ck_check_in_configs_at_least_one_channel",
        "check_in_configs",
        type_="check",
    )
    op.drop_column("check_in_configs", "push_enabled")
    op.drop_column("check_in_configs", "email_enabled")
