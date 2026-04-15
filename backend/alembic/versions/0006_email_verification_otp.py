"""add email verification fields for otp onboarding

Revision ID: 0006_email_verification_otp
Revises: 0005_responder_acknowledgments
Create Date: 2026-04-15 21:40:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0006_email_verification_otp"
down_revision = "0005_responder_acknowledgments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "owners",
        sa.Column("email_verified", sa.Boolean(), nullable=True, server_default=sa.false()),
    )
    op.add_column(
        "owners",
        sa.Column("email_verification_code_hash", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "owners",
        sa.Column("email_verification_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "owners",
        sa.Column("email_verification_sent_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Existing users remain unaffected by OTP rollout.
    op.execute("UPDATE owners SET email_verified = TRUE")

    op.alter_column(
        "owners",
        "email_verified",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.false(),
    )


def downgrade() -> None:
    op.drop_column("owners", "email_verification_sent_at")
    op.drop_column("owners", "email_verification_expires_at")
    op.drop_column("owners", "email_verification_code_hash")
    op.drop_column("owners", "email_verified")
