# -*- coding: utf-8 -*-
"""
================================================================================
PYDANTIC SCHEMAS - STUDY PLAN
================================================================================
Verzija: 1.0.0
================================================================================
"""

from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import List, Optional


# ============================================================
# STUDY PLAN
# ============================================================


class StudyPlanBase(BaseModel):
    daily_quiz_goal: int = Field(1, ge=1, le=20, description="Cilj: kvizova dnevno")
    weekly_quiz_goal: int = Field(5, ge=1, le=50, description="Cilj: kvizova nedeljno")
    session_duration_min: int = Field(
        20, ge=5, le=180, description="Trajanje sesije (minuti)"
    )
    study_days: List[int] = Field(
        default=[1, 2, 3, 4, 5], description="Dani u nedelji: 0=ned, 1=pon...6=sub"
    )
    reminder_enabled: bool = False
    reminder_time: str = Field("09:00", pattern=r"^\d{2}:\d{2}$")
    notes: Optional[str] = None


class StudyPlanCreate(StudyPlanBase):
    pass


class StudyPlanUpdate(BaseModel):
    daily_quiz_goal: Optional[int] = Field(None, ge=1, le=20)
    weekly_quiz_goal: Optional[int] = Field(None, ge=1, le=50)
    session_duration_min: Optional[int] = Field(None, ge=5, le=180)
    study_days: Optional[List[int]] = None
    reminder_enabled: Optional[bool] = None
    reminder_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class StudyPlanResponse(StudyPlanBase):
    id: str
    user_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# STUDY PLAN ITEM
# ============================================================


class StudyPlanItemCreate(BaseModel):
    quiz_id: str
    scheduled_for: date
    priority: int = Field(1, ge=1, le=3, description="1=normalan, 2=visok, 3=kritičan")
    notes: Optional[str] = None


class StudyPlanItemUpdate(BaseModel):
    scheduled_for: Optional[date] = None
    priority: Optional[int] = Field(None, ge=1, le=3)
    notes: Optional[str] = None


class QuizBrief(BaseModel):
    id: str
    title: str
    total_questions: int
    status: str

    class Config:
        from_attributes = True


class StudyPlanItemResponse(BaseModel):
    id: str
    plan_id: str
    quiz_id: str
    quiz: Optional[QuizBrief] = None
    scheduled_for: date
    priority: int
    notes: Optional[str] = None
    is_completed: bool
    completed_at: Optional[datetime] = None
    attempt_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CompleteItemRequest(BaseModel):
    attempt_id: Optional[str] = None


# ============================================================
# STUDY PLAN + ITEMS (puna slika)
# ============================================================


class StudyPlanWithItems(StudyPlanResponse):
    items: List[StudyPlanItemResponse] = []


# ============================================================
# PROGRESS / STATISTIKE
# ============================================================


class StudyPlanProgress(BaseModel):
    """Nedeljni/dnevni progres prema planu."""

    plan: StudyPlanResponse

    # Tekuća nedelja
    week_completed: int
    week_goal: int
    week_pct: float

    # Danas
    today_completed: int
    today_goal: int
    today_items: List[StudyPlanItemResponse] = []

    # Naredni zakazani kvizovi
    upcoming_items: List[StudyPlanItemResponse] = []

    # Streak (uzastopni dani sa bar jednim završenim kviizom)
    current_streak: int
