# -*- coding: utf-8 -*-
"""
================================================================================
ALEMBIC MIGRATION 002 - QUIZ TABLES
================================================================================
Kreira tabele za kviz sistem:
  - quizzes
  - questions
  - quiz_attempts
  - quiz_answers

Revision: 002
Date: 2026-02-28
================================================================================
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enum tipovi
    op.execute("""
        CREATE TYPE quiz_status AS ENUM ('generating', 'ready', 'error')
    """)
    op.execute("""
        CREATE TYPE question_type AS ENUM ('multiple_choice', 'checkbox', 'true_false')
    """)

    # quizzes
    op.create_table(
        'quizzes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('total_questions', sa.Integer, default=0),
        sa.Column('time_limit', sa.Integer, nullable=True),
        sa.Column('passing_score', sa.Integer, default=60),
        sa.Column('status', sa.Enum('generating', 'ready', 'error', name='quiz_status'), default='generating'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index('ix_quizzes_document_id', 'quizzes', ['document_id'])
    op.create_index('ix_quizzes_user_id', 'quizzes', ['user_id'])

    # questions
    op.create_table(
        'questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('quiz_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quizzes.id'), nullable=False),
        sa.Column('question_text', sa.Text, nullable=False),
        sa.Column('question_type', sa.Enum('multiple_choice', 'checkbox', 'true_false', name='question_type'), nullable=False, default='multiple_choice'),
        sa.Column('options', postgresql.JSON, nullable=False, server_default='[]'),
        sa.Column('correct_answer', sa.Text, nullable=False),
        sa.Column('explanation', sa.Text),
        sa.Column('points', sa.Integer, default=1),
        sa.Column('order_index', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_questions_quiz_id', 'questions', ['quiz_id'])

    # quiz_attempts
    op.create_table(
        'quiz_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('quiz_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quizzes.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('score', sa.Integer, default=0),
        sa.Column('total_points', sa.Integer, default=0),
        sa.Column('percentage', sa.Float, default=0.0),
        sa.Column('passed', sa.Boolean, default=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_quiz_attempts_quiz_id', 'quiz_attempts', ['quiz_id'])
    op.create_index('ix_quiz_attempts_user_id', 'quiz_attempts', ['user_id'])

    # quiz_answers
    op.create_table(
        'quiz_answers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('attempt_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quiz_attempts.id'), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('questions.id'), nullable=False),
        sa.Column('user_answer', sa.Text, nullable=False),
        sa.Column('is_correct', sa.Boolean, default=False),
        sa.Column('points_earned', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_quiz_answers_attempt_id', 'quiz_answers', ['attempt_id'])


def downgrade() -> None:
    op.drop_table('quiz_answers')
    op.drop_table('quiz_attempts')
    op.drop_table('questions')
    op.drop_table('quizzes')
    op.execute('DROP TYPE IF EXISTS question_type')
    op.execute('DROP TYPE IF EXISTS quiz_status')
