"""add pet documents table

Revision ID: 0008_pet_documents
Revises: 0007_notification_channels
Create Date: 2026-04-18 12:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "0008_pet_documents"
down_revision = "0007_notification_channels"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pet_documents",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "owner_id",
            sa.String(length=64),
            sa.ForeignKey("owners.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "pet_id",
            sa.String(length=64),
            sa.ForeignKey("pets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_pet_documents_owner_pet",
        "pet_documents",
        ["owner_id", "pet_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_pet_documents_owner_pet", table_name="pet_documents")
    op.drop_table("pet_documents")
