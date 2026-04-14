"""add auth fields

Revision ID: 0002_auth
Revises: 0001_initial
Create Date: 2026-04-15 12:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_auth"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("owners", sa.Column("password_hash", sa.String(length=255), nullable=False))
    op.add_column(
        "pets",
        sa.Column("emergency_access_token", sa.String(length=64), nullable=True, unique=True),
    )


def downgrade() -> None:
    op.drop_column("pets", "emergency_access_token")
    op.drop_column("owners", "password_hash")
