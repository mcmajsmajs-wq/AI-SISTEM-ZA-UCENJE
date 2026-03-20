# -*- coding: utf-8 -*-
"""
============================================================================
ALEMBIC MIGRATION 007 - QUIZ TARGET QUESTIONS
============================================================================
Dodaje target_questions kolonu za pracenje ocekivanog broja pitanja.

Revision: 007
Date: 2026-03-13
============================================================================
"""

from alembic import op
import sqlalchemy as sa

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('quizzes', sa.Column('target_questions', sa.Integer, default=0, nullable=True))


def downgrade() -> None:
    op.drop_column('quizzes', 'target_questions')
