# -*- coding: utf-8 -*-
"""
================================================================================
STUDY PLAN ENDPOINTS
================================================================================
Lični plan učenja korisnika — ciljevi, dani, zakazani kvizovi.

Verzija: 1.0.0
================================================================================
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, datetime, timezone, timedelta
from typing import Optional, List
import logging

from app.db.session import get_db
from app.db.models.study_plan import StudyPlan, StudyPlanItem
from app.db.models.quiz import Quiz
from app.db.models.user import User
from app.schemas.study_plan import (
    StudyPlanCreate,
    StudyPlanUpdate,
    StudyPlanResponse,
    StudyPlanWithItems,
    StudyPlanItemCreate,
    StudyPlanItemUpdate,
    StudyPlanItemResponse,
    CompleteItemRequest,
    StudyPlanProgress,
    QuizBrief,
)
from app.services.auth import get_current_user
from app.core.posthog import posthog_client

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================
# HELPERS
# ============================================================


def plan_to_response(plan: StudyPlan) -> StudyPlanResponse:
    return StudyPlanResponse(
        id=str(plan.id),
        user_id=str(plan.user_id),
        daily_quiz_goal=plan.daily_quiz_goal,
        weekly_quiz_goal=plan.weekly_quiz_goal,
        session_duration_min=plan.session_duration_min,
        study_days=plan.study_days or [1, 2, 3, 4, 5],
        reminder_enabled=plan.reminder_enabled,
        reminder_time=plan.reminder_time,
        notes=plan.notes,
        is_active=plan.is_active,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


def item_to_response(item: StudyPlanItem) -> StudyPlanItemResponse:
    quiz_brief = None
    if item.quiz:
        quiz_brief = QuizBrief(
            id=str(item.quiz.id),
            title=item.quiz.title,
            total_questions=item.quiz.total_questions,
            status=item.quiz.status,
        )
    return StudyPlanItemResponse(
        id=str(item.id),
        plan_id=str(item.plan_id),
        quiz_id=str(item.quiz_id),
        quiz=quiz_brief,
        scheduled_for=item.scheduled_for,
        priority=item.priority,
        notes=item.notes,
        is_completed=item.is_completed,
        completed_at=item.completed_at,
        attempt_id=str(item.attempt_id) if item.attempt_id else None,
        created_at=item.created_at,
    )


# ============================================================
# CRUD PLAN
# ============================================================


@router.get("/me", response_model=StudyPlanWithItems)
async def get_my_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dohvata plan korisnika (kreira prazan ako ne postoji)."""
    plan = db.query(StudyPlan).filter(StudyPlan.user_id == current_user.id).first()
    if not plan:
        plan = StudyPlan(user_id=current_user.id)
        db.add(plan)
        db.commit()
        db.refresh(plan)

    return StudyPlanWithItems(
        **plan_to_response(plan).model_dump(),
        items=[item_to_response(i) for i in plan.items],
    )


@router.put("/me", response_model=StudyPlanResponse)
async def update_my_plan(
    data: StudyPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ažurira ciljeve i podešavanja plana."""
    plan = db.query(StudyPlan).filter(StudyPlan.user_id == current_user.id).first()
    if not plan:
        plan = StudyPlan(user_id=current_user.id)
        db.add(plan)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(plan, field, value)

    db.commit()
    db.refresh(plan)
    return plan_to_response(plan)


@router.post(
    "/me", response_model=StudyPlanResponse, status_code=status.HTTP_201_CREATED
)
async def create_my_plan(
    data: StudyPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Kreira novi plan (ili zamenjuje postojeći)."""
    existing = db.query(StudyPlan).filter(StudyPlan.user_id == current_user.id).first()
    if existing:
        for field, value in data.model_dump().items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return plan_to_response(existing)

    plan = StudyPlan(user_id=current_user.id, **data.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan_to_response(plan)


# ============================================================
# CRUD PLAN ITEMS
# ============================================================


@router.get("/me/items", response_model=List[StudyPlanItemResponse])
async def list_plan_items(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    only_pending: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista stavki plana sa opcionim filterom po datumu."""
    plan = db.query(StudyPlan).filter(StudyPlan.user_id == current_user.id).first()
    if not plan:
        return []

    query = db.query(StudyPlanItem).filter(StudyPlanItem.plan_id == plan.id)

    if from_date:
        query = query.filter(StudyPlanItem.scheduled_for >= from_date)
    if to_date:
        query = query.filter(StudyPlanItem.scheduled_for <= to_date)
    if only_pending:
        query = query.filter(StudyPlanItem.is_completed is False)

    items = query.order_by(
        StudyPlanItem.scheduled_for, StudyPlanItem.priority.desc()
    ).all()

    return [item_to_response(i) for i in items]


@router.post(
    "/me/items",
    response_model=StudyPlanItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_plan_item(
    data: StudyPlanItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dodaje kviz u plan za određeni datum."""
    plan = db.query(StudyPlan).filter(StudyPlan.user_id == current_user.id).first()
    if not plan:
        plan = StudyPlan(user_id=current_user.id)
        db.add(plan)
        db.commit()
        db.refresh(plan)

    # Proveri da li kviz pripada korisniku
    quiz = (
        db.query(Quiz)
        .filter(Quiz.id == data.quiz_id, Quiz.user_id == current_user.id)
        .first()
    )
    if not quiz:
        raise HTTPException(status_code=404, detail="Kviz nije pronađen")

    item = StudyPlanItem(
        plan_id=plan.id,
        quiz_id=data.quiz_id,
        scheduled_for=data.scheduled_for,
        priority=data.priority,
        notes=data.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item_to_response(item)


@router.put("/me/items/{item_id}", response_model=StudyPlanItemResponse)
async def update_plan_item(
    item_id: str,
    data: StudyPlanItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Menja datum, prioritet ili belešku stavke."""
    plan = db.query(StudyPlan).filter(StudyPlan.user_id == current_user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan nije pronađen")

    item = (
        db.query(StudyPlanItem)
        .filter(StudyPlanItem.id == item_id, StudyPlanItem.plan_id == plan.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Stavka nije pronađena")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item_to_response(item)


@router.post("/me/items/{item_id}/complete", response_model=StudyPlanItemResponse)
async def complete_plan_item(
    item_id: str,
    data: CompleteItemRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Označava stavku kao završenu."""
    plan = db.query(StudyPlan).filter(StudyPlan.user_id == current_user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan nije pronađen")

    item = (
        db.query(StudyPlanItem)
        .filter(StudyPlanItem.id == item_id, StudyPlanItem.plan_id == plan.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Stavka nije pronađena")

    item.is_completed = True
    item.completed_at = datetime.now(timezone.utc)
    if data.attempt_id:
        item.attempt_id = data.attempt_id

    db.commit()
    db.refresh(item)

    posthog_client.capture(
        "study plan item completed",
        distinct_id=str(current_user.id),
        properties={
            "quiz_id": str(item.quiz_id),
            "priority": item.priority,
            "has_attempt": bool(item.attempt_id),
        },
    )

    return item_to_response(item)


@router.delete("/me/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Briše stavku iz plana."""
    plan = db.query(StudyPlan).filter(StudyPlan.user_id == current_user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan nije pronađen")

    item = (
        db.query(StudyPlanItem)
        .filter(StudyPlanItem.id == item_id, StudyPlanItem.plan_id == plan.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Stavka nije pronađena")

    db.delete(item)
    db.commit()


# ============================================================
# PROGRESS
# ============================================================


@router.get("/me/progress", response_model=StudyPlanProgress)
async def get_plan_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Vraća progres korisnika prema planu:
    - Nedeljni cilj vs ostvareno
    - Dnevni cilj vs ostvareno
    - Naredni zakazani kvizovi
    - Streak
    """
    plan = db.query(StudyPlan).filter(StudyPlan.user_id == current_user.id).first()
    if not plan:
        plan = StudyPlan(user_id=current_user.id)
        db.add(plan)
        db.commit()
        db.refresh(plan)

    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Ponedeljak
    week_end = week_start + timedelta(days=6)

    # Nedeljni progres
    week_items = (
        db.query(StudyPlanItem)
        .filter(
            StudyPlanItem.plan_id == plan.id,
            StudyPlanItem.scheduled_for >= week_start,
            StudyPlanItem.scheduled_for <= week_end,
        )
        .all()
    )
    week_completed = sum(1 for i in week_items if i.is_completed)

    # Dnevni progres
    today_items = (
        db.query(StudyPlanItem)
        .filter(
            StudyPlanItem.plan_id == plan.id,
            StudyPlanItem.scheduled_for == today,
        )
        .order_by(StudyPlanItem.priority.desc())
        .all()
    )
    today_completed = sum(1 for i in today_items if i.is_completed)

    # Naredni zakazani (sledeća 7 dana, nezavršeni)
    upcoming = (
        db.query(StudyPlanItem)
        .filter(
            StudyPlanItem.plan_id == plan.id,
            StudyPlanItem.scheduled_for >= today,
            StudyPlanItem.is_completed is False,
        )
        .order_by(StudyPlanItem.scheduled_for, StudyPlanItem.priority.desc())
        .limit(10)
        .all()
    )

    # Streak — uzastopni dani unazad sa bar jednim završenim
    streak = 0
    check_date = today
    while True:
        day_items = (
            db.query(StudyPlanItem)
            .filter(
                StudyPlanItem.plan_id == plan.id,
                StudyPlanItem.scheduled_for == check_date,
                StudyPlanItem.is_completed is True,
            )
            .count()
        )
        if day_items == 0 and check_date < today:
            break
        if day_items > 0:
            streak += 1
        check_date -= timedelta(days=1)
        if (today - check_date).days > 365:
            break

    week_pct = (
        round((week_completed / plan.weekly_quiz_goal) * 100, 1)
        if plan.weekly_quiz_goal
        else 0
    )

    return StudyPlanProgress(
        plan=plan_to_response(plan),
        week_completed=week_completed,
        week_goal=plan.weekly_quiz_goal,
        week_pct=min(week_pct, 100.0),
        today_completed=today_completed,
        today_goal=plan.daily_quiz_goal,
        today_items=[item_to_response(i) for i in today_items],
        upcoming_items=[item_to_response(i) for i in upcoming],
        current_streak=streak,
    )
