"""add notification channel and refine notification types

Revision ID: 0007_notification_channels
Revises: 0006_email_verification_otp
Create Date: 2026-04-16 02:20:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0007_notification_channels"
down_revision = "0006_email_verification_otp"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notification_logs", sa.Column("channel", sa.String(length=16), nullable=True))

    op.execute("UPDATE notification_logs SET channel = 'email' WHERE channel IS NULL")
    op.execute(
        """
        UPDATE notification_logs
        SET notification_type = CASE
            WHEN notification_type = 'reminder' THEN 'owner_reminder'
            WHEN notification_type = 'escalation_alert' THEN 'emergency_contact_escalation'
            ELSE notification_type
        END
        """
    )

    op.alter_column("notification_logs", "channel", nullable=False)


def downgrade() -> None:
    op.execute(
        """
        UPDATE notification_logs
        SET notification_type = CASE
            WHEN notification_type = 'owner_reminder' THEN 'reminder'
            WHEN notification_type = 'emergency_contact_escalation' THEN 'escalation_alert'
            ELSE notification_type
        END
        """
    )
    op.drop_column("notification_logs", "channel")
