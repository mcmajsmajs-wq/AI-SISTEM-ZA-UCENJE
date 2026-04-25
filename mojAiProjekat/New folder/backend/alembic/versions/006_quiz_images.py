# -*- coding: utf-8 -*-
"""
============================================================================
ALEMBIC MIGRATION 006 - QUIZ IMAGES
============================================================================
Dodaje podrsku za slike u kviz pitanjima:
  - image_url i image_caption kolone u questions tabeli
  - nova quiz_images tabela za cuvanje ekstrahovanih slika iz PDF

Revision: 006
Date: 2026-03-13
============================================================================
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns to questions table
    op.add_column('questions', sa.Column('image_url', sa.Text, nullable=True))
    op.add_column('questions', sa.Column('image_caption', sa.Text, nullable=True))
    
    # Create quiz_images table
    op.create_table(
        'quiz_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=False, index=True),
        sa.Column('storage_path', sa.Text, nullable=False),
        sa.Column('image_url', sa.Text, nullable=False),
        sa.Column('mime_type', sa.String(50), sa.Text, default='image/jpeg'),
        sa.Column('file_size', sa.Integer),
        sa.Column('page_number', sa.Integer),
        sa.Column('caption', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('quiz_images')
    op.drop_column('questions', 'image_caption')
    op.drop_column('questions', 'image_url')
