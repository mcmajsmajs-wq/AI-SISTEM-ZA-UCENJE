"""Initial migration with all models

Revision ID: 001
Revises: 
Create Date: 2026-02-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('role', sa.Enum('admin', 'user', name='user_role'), default='user'),
        sa.Column('timezone', sa.String(50), default='Europe/Belgrade'),
        sa.Column('language', sa.String(10), default='sr'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    
    # Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.Text, nullable=False),
        sa.Column('refresh_token', sa.Text),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_user_sessions_user_id', 'user_sessions', ['user_id'])
    
    # Create files table
    op.create_table(
        'files',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('original_filename', sa.String(500), nullable=False),
        sa.Column('storage_path', sa.Text, nullable=False),
        sa.Column('file_size', sa.BigInteger, nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('checksum', sa.String(64), nullable=False),
        sa.Column('status', sa.Enum('uploaded', 'processing', 'completed', 'error', 'deleted', name='file_status'), default='uploaded'),
        sa.Column('metadata', sa.JSON, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_files_user_id', 'files', ['user_id'])
    
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('files.id'), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('total_pages', sa.Integer),
        sa.Column('total_chunks', sa.Integer, default=0),
        sa.Column('status', sa.Enum('pending', 'processing', 'translating', 'completed', 'error', name='document_status'), default='pending'),
        sa.Column('source_language', sa.String(10), default='en'),
        sa.Column('target_language', sa.String(10), default='sr'),
        sa.Column('metadata', sa.JSON, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index('ix_documents_user_id', 'documents', ['user_id'])
    
    # Create chunks table
    op.create_table(
        'chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('sequence_number', sa.Integer, nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('translated_content', sa.Text),
        sa.Column('token_count', sa.Integer),
        sa.Column('heading_level', sa.Integer, default=0),
        sa.Column('parent_heading', sa.String(500)),
        sa.Column('is_translated', sa.Integer, default=0),
        sa.Column('is_reviewed', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index('ix_chunks_document_id', 'chunks', ['document_id'])


def downgrade() -> None:
    op.drop_table('chunks')
    op.drop_table('documents')
    op.drop_table('files')
    op.drop_table('user_sessions')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS user_role')
    op.execute('DROP TYPE IF EXISTS file_status')
    op.execute('DROP TYPE IF EXISTS document_status')
