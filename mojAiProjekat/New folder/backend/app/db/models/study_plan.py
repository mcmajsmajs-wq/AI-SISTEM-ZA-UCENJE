# -*- coding: utf-8 -*-
"""
================================================================================
SQLALCHEMY MODELS - STUDY PLAN (Lični plan učenja)
================================================================================
StudyPlan  — korisnikov lični plan: ciljevi, dani, trajanje sesije.
StudyPlanItem — konkretna stavka plana: koji kviz, kada, status.

Verzija: 1.0.0
================================================================================
"""

from sqlalchemy import (
    Column, String, Integer, Text, DateTime, Boolean, JSON, ForeignKey, Date
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class StudyPlan(Base):
    """
    Lični plan učenja korisnika.
    Jedan korisnik ima jedan aktivan plan.
    """
    __tablename__ = "study_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)

    # Ciljevi
    daily_quiz_goal = Column(Integer, default=1)        # kvizova dnevno
    weekly_quiz_goal = Column(Integer, default=5)       # kvizova nedeljno
    session_duration_min = Column(Integer, default=20)  # minuta po sesiji

    # Dani u nedelji (JSON lista: [0=ned, 1=pon, 2=uto, 3=sre, 4=čet, 5=pet, 6=sub])
    study_days = Column(JSON, default=lambda: [1, 2, 3, 4, 5])  # radni dani

    # Reminder
    reminder_enabled = Column(Boolean, default=False)
    reminder_time = Column(String(5), default="09:00")  # "HH:MM"

    # Beleška / motivacioni tekst
    notes = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relacije
    items = relationship(
        "StudyPlanItem",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="StudyPlanItem.scheduled_for"
    )

    def __repr__(self):
        return f"<StudyPlan(user={self.user_id}, daily={self.daily_quiz_goal})>"


class StudyPlanItem(Base):
    """
    Jedna stavka u planu — konkretan kviz zakazano za određeni datum.
    """
    __tablename__ = "study_plan_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("study_plans.id"), nullable=False, index=True)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=False)

    scheduled_for = Column(Date, nullable=False)       # datum kada treba uraditi
    priority = Column(Integer, default=1)              # 1=normalan, 2=visok, 3=kritičan
    notes = Column(Text, nullable=True)

    # Status
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    attempt_id = Column(UUID(as_uuid=True), nullable=True)  # poslednji pokušaj

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relacije
    plan = relationship("StudyPlan", back_populates="items")
    quiz = relationship("Quiz", lazy="joined")

    def __repr__(self):
        return f"<StudyPlanItem(quiz={self.quiz_id}, date={self.scheduled_for}, done={self.is_completed})>"
