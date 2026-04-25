# -*- coding: utf-8 -*-
"""
================================================================================
SQLALCHEMY MODELS - QUIZ
================================================================================
Modeli za kviz sistem: Quiz, Question, QuizAttempt, Answer.

Verzija: 1.0.0
================================================================================
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Enum, JSON, ForeignKey, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class Quiz(Base):
    """
    ================================================================================
    QUIZ MODEL
    ================================================================================
    Reprezentuje kviz kreiran iz dokumenta.
    ================================================================================
    """
    __tablename__ = "quizzes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    title = Column(String(500), nullable=False)
    description = Column(Text)
    
    total_questions = Column(Integer, default=0)
    time_limit = Column(Integer, default=0)
    passing_score = Column(Integer, default=70)
    max_attempts = Column(Integer, default=3)
    
    difficulty = Column(
        Enum("easy", "medium", "hard", "mixed", name="quiz_difficulty"),
        default="medium"
    )
    
    question_types = Column(JSON, default=list)
    status = Column(
        Enum("draft", "published", "archived", name="quiz_status"),
        default="draft"
    )
    
    attempts_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))
    
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Quiz(id={self.id}, title={self.title}, questions={self.total_questions})>"


class Question(Base):
    """
    ================================================================================
    QUESTION MODEL
    ================================================================================
    Reprezentira pitanje u kvizu.
    ================================================================================
    """
    __tablename__ = "questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=False)
    chunk_id = Column(UUID(as_uuid=True), nullable=True)
    
    question_text = Column(Text, nullable=False)
    question_type = Column(
        Enum("multiple_choice", "checkbox", "true_false", "short_answer", name="question_type"),
        default="multiple_choice"
    )
    
    options = Column(JSON, default=list)
    correct_answer = Column(String(500), nullable=False)
    correct_answers = Column(JSON, default=list)
    
    explanation = Column(Text)
    hint = Column(Text)
    
    points = Column(Integer, default=1)
    order = Column(Integer, default=0)
    difficulty = Column(
        Enum("easy", "medium", "hard", name="question_difficulty"),
        default="medium"
    )
    
    source_text = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    quiz = relationship("Quiz", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Question(id={self.id}, type={self.question_type}, points={self.points})>"


class QuizAttempt(Base):
    """
    ================================================================================
    QUIZ ATTEMPT MODEL
    ================================================================================
    Reprezentira pokušaj rešavanja kviza.
    ================================================================================
    """
    __tablename__ = "quiz_attempts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    score = Column(Integer, default=0)
    total_points = Column(Integer, default=0)
    percentage = Column(Float, default=0.0)
    passed = Column(Boolean, default=False)
    
    correct_answers = Column(Integer, default=0)
    wrong_answers = Column(Integer, default=0)
    skipped_answers = Column(Integer, default=0)
    
    time_spent = Column(Integer, default=0)
    
    status = Column(
        Enum("in_progress", "completed", "abandoned", name="attempt_status"),
        default="in_progress"
    )
    
    answers_data = Column(JSON, default=dict)
    
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    quiz = relationship("Quiz", back_populates="attempts")
    answers = relationship("Answer", back_populates="attempt", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<QuizAttempt(id={self.id}, score={self.score}/{self.total_points})>"


class Answer(Base):
    """
    ================================================================================
    ANSWER MODEL
    ================================================================================
    Reprezentira odgovor na pitanje u pokušaju.
    ================================================================================
    """
    __tablename__ = "answers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id = Column(UUID(as_uuid=True), ForeignKey("quiz_attempts.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    
    selected_answer = Column(String(500))
    selected_answers = Column(JSON, default=list)
    text_answer = Column(Text)
    
    is_correct = Column(Boolean, default=False)
    points_earned = Column(Integer, default=0)
    
    time_spent = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    attempt = relationship("QuizAttempt", back_populates="answers")
    question = relationship("Question", back_populates="answers")
    
    def __repr__(self):
        return f"<Answer(id={self.id}, correct={self.is_correct}, points={self.points_earned})>"
