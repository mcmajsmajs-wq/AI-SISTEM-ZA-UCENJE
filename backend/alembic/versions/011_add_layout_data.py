# -*- coding: utf-8 -*-
"""Add layout_data JSON column to chunks table

Revision ID: 011
Revises: 010
Create Date: 2026-05-26 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers, used by Alembic.
revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "chunks",
        sa.Column("layout_data", postgresql.JSON, nullable=True),
    )


def downgrade():
    op.drop_column("chunks", "layout_data")
