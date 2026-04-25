# -*- coding: utf-8 -*-
"""
================================================================================
ALEMBIC MIGRATION - QUIZ TABLES
================================================================================
Adds Quiz, Question, QuizAttempt, and Answer tables.

Revision ID: 002
Revises: 001
Create Date: 2026-02-19
================================================================================
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create quiz_status enum
    op.execute("""
        CREATE TYPE quiz_status AS ENUM ('draft', 'published', 'archived')
    """)
    
    # Create quiz_difficulty enum
    op.execute("""
        CREATE TYPE quiz_difficulty AS ENUM ('easy', 'medium', 'hard', 'mixed')
    """)
    
    # Create question_type enum
    op.execute("""
        CREATE TYPE question_type AS ENUM ('multiple_choice', 'checkbox', 'true_false', 'short_answer')
    """)
    
    # Create question_difficulty enum
    op.execute("""
        CREATE TYPE question_difficulty AS ENUM ('easy', 'medium', 'hard')
    """)
    
    # Create attempt_status enum
    op.execute("""
        CREATE TYPE attempt_status AS ENUM ('in_progress', 'completed', 'abandoned')
    """)
    
    # Create quizzes table
    op.create_table(
        'quizzes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('total_questions', sa.Integer, default=0),
        sa.Column('time_limit', sa.Integer, default=0),
        sa.Column('passing_score', sa.Integer, default=70),
        sa.Column('max_attempts', sa.Integer, default=3),
        sa.Column('difficulty', postgresql.ENUM('easy', 'medium', 'hard', 'mixed', name='quiz_difficulty', create_type=False)),
        sa.Column('question_types', postgresql.JSON, default=[]),
        sa.Column('status', postgresql.ENUM('draft', 'published', 'archived', name='quiz_status', create_type=False)),
        sa.Column('attempts_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('published_at', sa.DateTime(timezone=True)),
    )
    
    op.create_index('ix_quizzes_user_id', 'quizzes', ['user_id'])
    
    # Create questions table
    op.create_table(
        'questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('quiz_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quizzes.id'), nullable=False),
        sa.Column('chunk_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('question_text', sa.Text, nullable=False),
        sa.Column('question_type', postgresql.ENUM('multiple_choice', 'checkbox', 'true_false', 'short_answer', name='question_type', create_type=False)),
        sa.Column('options', postgresql.JSON, default=[]),
        sa.Column('correct_answer', sa.String(500), nullable=False),
        sa.Column('correct_answers', postgresql.JSON, default=[]),
        sa.Column('explanation', sa.Text),
        sa.Column('hint', sa.Text),
        sa.Column('points', sa.Integer, default=1),
        sa.Column('order', sa.Integer, default=0),
        sa.Column('difficulty', postgresql.ENUM('easy', 'medium', 'hard', name='question_difficulty', create_type=False)),
        sa.Column('source_text', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    op.create_index('ix_questions_quiz_id', 'questions', ['quiz_id'])
    
    # Create quiz_attempts table
    op.create_table(
        'quiz_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('quiz_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quizzes.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('score', sa.Integer, default=0),
        sa.Column('total_points', sa.Integer, default=0),
        sa.Column('percentage', sa.Float, default=0.0),
        sa.Column('passed', sa.Boolean, default=False),
        sa.Column('correct_answers', sa.Integer, default=0),
        sa.Column('wrong_answers', sa.Integer, default=0),
        sa.Column('skipped_answers', sa.Integer, default=0),
        sa.Column('time_spent', sa.Integer, default=0),
        sa.Column('status', postgresql.ENUM('in_progress', 'completed', 'abandoned', name='attempt_status', create_type=False)),
        sa.Column('answers_data', postgresql.JSON, default={}),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
    )
    
    op.create_index('ix_quiz_attempts_user_id', 'quiz_attempts', ['user_id'])
    op.create_index('ix_quiz_attempts_quiz_id', 'quiz_attempts', ['quiz_id'])
    
    # Create answers table
    op.create_table(
        'answers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('attempt_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quiz_attempts.id'), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('questions.id'), nullable=False),
        sa.Column('selected_answer', sa.String(500)),
        sa.Column('selected_answers', postgresql.JSON, default=[]),
        sa.Column('text_answer', sa.Text),
        sa.Column('is_correct', sa.Boolean, default=False),
        sa.Column('points_earned', sa.Integer, default=0),
        sa.Column('time_spent', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    op.create_index('ix_answers_attempt_id', 'answers', ['attempt_id'])
    op.create_index('ix_answers_question_id', 'answers', ['question_id'])


def downgrade():
    op.drop_table('answers')
    op.drop_table('quiz_attempts')
    op.drop_table('questions')
    op.drop_table('quizzes')
    
    op.execute("DROP TYPE IF EXISTS attempt_status")
    op.execute("DROP TYPE IF EXISTS question_difficulty")
    op.execute("DROP TYPE IF EXISTS question_type")
    op.execute("DROP TYPE IF EXISTS quiz_difficulty")
    op.execute("DROP TYPE IF EXISTS quiz_status")
