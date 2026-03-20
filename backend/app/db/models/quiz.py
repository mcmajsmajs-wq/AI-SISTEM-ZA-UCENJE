# -*- coding: utf-8 -*-
"""
================================================================================
SQLALCHEMY MODELS - QUIZ SISTEM
================================================================================
Modeli za kviz sistem: Quiz, Question, QuizAttempt, QuizAnswer.

Verzija: 1.0.0
================================================================================
"""

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Boolean, Enum, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class Quiz(Base):
    """
    Kviz generisan iz dokumenta.
    """
    __tablename__ = "quizzes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    title = Column(String(500), nullable=False)
    description = Column(Text)
    subject_area = Column(String(100))  # Oblast dokumenta (matematika, fizika, hemija...)
    total_questions = Column(Integer, default=0)
    target_questions = Column(Integer, default=0)  # očekivan broj pitanja
    time_limit = Column(Integer, nullable=True)  # sekunde, None = bez limita
    passing_score = Column(Integer, default=60)  # procenat za prolaz
    shuffle_questions = Column(Boolean, default=False)  # mešanje redosleda pitanja

    status = Column(
        Enum("generating", "ready", "error", name="quiz_status"),
        default="generating"
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relacije
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan", order_by="Question.order_index")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Quiz(id={self.id}, title={self.title}, questions={self.total_questions})>"


class Question(Base):
    """
    Pitanje u kviizu.
    Podržava: multiple_choice, checkbox (više tačnih), true_false.
    """
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=False, index=True)

    question_text = Column(Text, nullable=False)
    question_type = Column(
        Enum("multiple_choice", "checkbox", "true_false", "fill_blank", "calculation", "step_by_step", "chemical_equation", name="question_type"),
        nullable=False,
        default="multiple_choice"
    )

    # options: lista string opcija (npr. ["A", "B", "C", "D"])
    options = Column(JSON, nullable=False, default=list)
    # correct_answer: za multiple_choice/true_false = jedna vrednost,
    #                 za checkbox = lista vrednosti kao JSON string
    correct_answer = Column(Text, nullable=False)

    # Dodatna polja za fill_blank tip pitanja
    exact_word = Column(Text)  # Tačna reč za fill_blank
    alternative_words = Column(JSON)  # Alternativni odgovori (sinonimi)
    case_insensitive = Column(Boolean, default=True)  # Da li je veličina slova bitna

    # Polja za calculation i step_by_step tipove
    formula = Column(Text)  # Formula za izračunavanje
    steps = Column(JSON)  # Koraci za step_by_step (lista stringova)

    explanation = Column(Text)
    points = Column(Integer, default=1)
    order_index = Column(Integer, default=0)
    
    # Image for question (stored in MinIO/S3)
    image_url = Column(Text)
    image_caption = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relacije
    quiz = relationship("Quiz", back_populates="questions")
    answers = relationship("QuizAnswer", back_populates="question", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Question(id={self.id}, type={self.question_type})>"


class QuizImage(Base):
    """
    Slike ekstrahovane iz PDF dokumenta za kviz pitanja.
    """
    __tablename__ = "quiz_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    
    # Image storage info
    storage_path = Column(Text, nullable=False)
    image_url = Column(Text, nullable=False)
    mime_type = Column(String(50), default="image/jpeg")
    file_size = Column(Integer)
    
    # Image metadata
    page_number = Column(Integer)
    caption = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    document = relationship("Document", backref="quiz_images")


class QuizAttempt(Base):
    """
    Pokušaj rešavanja kviza od strane korisnika.
    """
    __tablename__ = "quiz_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    score = Column(Integer, default=0)        # osvajeni poeni
    total_points = Column(Integer, default=0)  # maksimalni poeni
    percentage = Column(Float, default=0.0)
    passed = Column(Boolean, default=False)

    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relacije
    quiz = relationship("Quiz", back_populates="attempts")
    answers = relationship("QuizAnswer", back_populates="attempt", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<QuizAttempt(id={self.id}, quiz_id={self.quiz_id}, score={self.score}/{self.total_points})>"


class QuizAnswer(Base):
    """
    Odgovor korisnika na pitanje u pokušaju.
    """
    __tablename__ = "quiz_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id = Column(UUID(as_uuid=True), ForeignKey("quiz_attempts.id"), nullable=False, index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)

    user_answer = Column(Text, nullable=False)  # odgovor korisnika
    is_correct = Column(Boolean, default=False)
    points_earned = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relacije
    attempt = relationship("QuizAttempt", back_populates="answers")
    question = relationship("Question", back_populates="answers")

    def __repr__(self):
        return f"<QuizAnswer(id={self.id}, correct={self.is_correct})>"
