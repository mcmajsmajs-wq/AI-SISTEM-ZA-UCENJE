# -*- coding: utf-8 -*-
"""Add PDF export fields to Document model

Revision ID: 010
Revises: 009
Create Date: 2026-05-03 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers, used by Alembic.
revision = "010"
down_revision = "009_file_skills"
branch_labels = None
depends_on = None


def upgrade():
    # Create enum type for pdf_export_status if not exists
    pdf_export_status_enum = postgresql.ENUM(
        "pending",
        "processing",
        "completed",
        "failed",
        name="pdf_export_status",
        create_type=True,
    )
    pdf_export_status_enum.create(op.get_bind(), checkfirst=True)

    # Add new columns to documents table
    op.add_column(
        "documents",
        sa.Column("pdf_export_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("pdf_export_status", pdf_export_status_enum, nullable=True),
    )
    op.add_column(
        "documents", sa.Column("pdf_export_task_id", sa.String(255), nullable=True)
    )


def downgrade():
    # Drop columns
    op.drop_column("documents", "pdf_export_task_id")
    op.drop_column("documents", "pdf_export_status")
    op.drop_column("documents", "pdf_export_id")

    # Drop enum type
    pdf_export_status_enum = postgresql.ENUM(name="pdf_export_status")
    pdf_export_status_enum.drop(op.get_bind(), checkfirst=True)
