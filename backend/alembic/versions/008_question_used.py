# -*- coding: utf-8 -*-
"""
========================================================================
ALEMBIC MIGRATION 008 - QUESTION USED FLAG
========================================================================
Dodaje 'used' kolonu za pracenje da li je pitanje korisceno u kvizu.

Revision: 008
Date: 2026-03-28
========================================================================
"""

from alembic import op
import sqlalchemy as sa

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('questions', sa.Column('used', sa.Boolean, default=False, nullable=True))
    op.create_index('ix_questions_used', 'questions', ['used'])


def downgrade() -> None:
    op.drop_index('ix_questions_used', 'questions')
    op.drop_column('questions', 'used')
