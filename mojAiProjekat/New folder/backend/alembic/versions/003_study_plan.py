# -*- coding: utf-8 -*-
"""
================================================================================
ALEMBIC MIGRATION 003 - STUDY PLAN TABLES
================================================================================
Kreira tabele za lični plan učenja:
  - study_plans
  - study_plan_items

Revision: 003
Date: 2026-02-28
================================================================================
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # study_plans
    op.create_table(
        'study_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('daily_quiz_goal', sa.Integer, default=1),
        sa.Column('weekly_quiz_goal', sa.Integer, default=5),
        sa.Column('session_duration_min', sa.Integer, default=20),
        sa.Column('study_days', postgresql.JSON, nullable=True),
        sa.Column('reminder_enabled', sa.Boolean, default=False),
        sa.Column('reminder_time', sa.String(5), default='09:00'),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index('ix_study_plans_user_id', 'study_plans', ['user_id'])

    # study_plan_items
    op.create_table(
        'study_plan_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('study_plans.id'), nullable=False),
        sa.Column('quiz_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quizzes.id'), nullable=False),
        sa.Column('scheduled_for', sa.Date, nullable=False),
        sa.Column('priority', sa.Integer, default=1),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('is_completed', sa.Boolean, default=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('attempt_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_study_plan_items_plan_id', 'study_plan_items', ['plan_id'])
    op.create_index('ix_study_plan_items_scheduled_for', 'study_plan_items', ['scheduled_for'])


def downgrade() -> None:
    op.drop_table('study_plan_items')
    op.drop_table('study_plans')
