# -*- coding: utf-8 -*-
"""
================================================================================
ALEMBIC MIGRATION 004 - ADDITIONAL AI PROVIDERS
================================================================================
Dodaje kolone za dodatne AI provajdere:
  - ai_api_key_gemini   (Google Gemini)
  - ai_api_key_groq     (Groq - Llama/Mixtral)
  - ai_api_key_mistral  (Mistral AI)
  - ai_custom_base_url  (Custom OpenAI-compatible endpoint)
  - ai_api_key_custom   (API ključ za custom endpoint)

Revision: 004
Date: 2026-03-01
================================================================================
"""

from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('ai_api_key_gemini', sa.Text, nullable=True))
    op.add_column('users', sa.Column('ai_api_key_groq', sa.Text, nullable=True))
    op.add_column('users', sa.Column('ai_api_key_mistral', sa.Text, nullable=True))
    op.add_column('users', sa.Column('ai_custom_base_url', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('ai_api_key_custom', sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'ai_api_key_gemini')
    op.drop_column('users', 'ai_api_key_groq')
    op.drop_column('users', 'ai_api_key_mistral')
    op.drop_column('users', 'ai_custom_base_url')
    op.drop_column('users', 'ai_api_key_custom')
