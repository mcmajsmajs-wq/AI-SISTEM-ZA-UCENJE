# -*- coding: utf-8 -*-
"""
================================================================================
ALEMBIC MIGRATION 005 - NEW QUIZ QUESTION TYPES
================================================================================
Dodaje nove tipove pitanja za kviz sistem:
  - sequencing      (Sortiranje elemenata po redosledu)
  - categorization (Razvrstavanje u kategorije/buckets)
  - matching       (Povezivanje parova)
  - hotspot        (Klik na koordinate na slici)
  - odd_one_out    (Pronađi uljeza)
  - estimation     (Procena vrednosti - klizač)
  - matrix         (True/False matrica)

Takođe dodaje extra_data JSON kolonu za kompleksne tipove pitanja.

Revision: 005
Date: 2026-04-06
================================================================================
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add new enum values to question_type
    op.execute("""
        ALTER TYPE question_type ADD VALUE IF NOT EXISTS 'sequencing';
        ALTER TYPE question_type ADD VALUE IF NOT EXISTS 'categorization';
        ALTER TYPE question_type ADD VALUE IF NOT EXISTS 'matching';
        ALTER TYPE question_type ADD VALUE IF NOT EXISTS 'hotspot';
        ALTER TYPE question_type ADD VALUE IF NOT EXISTS 'odd_one_out';
        ALTER TYPE question_type ADD VALUE IF NOT EXISTS 'estimation';
        ALTER TYPE question_type ADD VALUE IF NOT EXISTS 'matrix';
    """)

    # 2. Add extra_data column to questions table
    op.add_column(
        "questions", sa.Column("extra_data", JSON, nullable=True, server_default="{}")
    )


def downgrade() -> None:
    # 1. Drop extra_data column
    op.drop_column("questions", "extra_data")
