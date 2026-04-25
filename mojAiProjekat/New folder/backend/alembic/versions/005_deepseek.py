# -*- coding: utf-8 -*-
"""
================================================================================
ALEMBIC MIGRATION 005 - DEEPSEEK AI PROVIDER
===============================================================================
Dodaje kolonu za DeepSeek AI provajder:
  - ai_api_key_deepseek  (DeepSeek API ključ)

Revision: 005
Date: 2026-03-10
================================================================================
"""

from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('ai_api_key_deepseek', sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'ai_api_key_deepseek')
