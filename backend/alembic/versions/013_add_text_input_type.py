# -*- coding: utf-8 -*-
"""
===============================================================================
ALEMBIC MIGRATION 013 - ADD TEXT_INPUT QUESTION TYPE
===============================================================================
Dodaje text_input tip pitanja u question_type enum.

Revision: 013
Revises: 012
Date: 2026-06-03
===============================================================================
"""

from alembic import op

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE question_type ADD VALUE IF NOT EXISTS 'text_input';")


def downgrade() -> None:
    pass
