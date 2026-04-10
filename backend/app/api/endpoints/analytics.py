# -*- coding: utf-8 -*-
"""
================================================================================
ANALYTICS ENDPOINTS
================================================================================
Statistike i analitika napretka korisnika.

Verzija: 1.0.0
================================================================================
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
import logging

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.quiz import Quiz, QuizAttempt
from app.db.models.study_plan import StudyPlan, StudyPlanItem
from app.db.models.document import Document
from app.services.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────────────────
# GET /analytics/me/overview
# ────────────────────────────────────────────────────────────────────────────────
@router.get("/me/overview")
async def get_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ukupne statistike korisnika."""

    total_attempts = (
        db.query(QuizAttempt).filter(QuizAttempt.user_id == current_user.id).count()
    )

    passed_attempts = (
        db.query(QuizAttempt)
        .filter(
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.passed is True,
        )
        .count()
    )

    avg_score_row = (
        db.query(func.avg(QuizAttempt.percentage))
        .filter(
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.completed_at is not None,
        )
        .scalar()
    )
    avg_score = round(float(avg_score_row or 0), 1)

    total_quizzes = db.query(Quiz).filter(Quiz.user_id == current_user.id).count()

    total_documents = (
        db.query(Document).filter(Document.user_id == current_user.id).count()
    )

    completed_plan_items = (
        db.query(StudyPlanItem)
        .join(StudyPlan)
        .filter(
            StudyPlan.user_id == current_user.id,
            StudyPlanItem.is_completed is True,
        )
        .count()
    )

    # Streak (posudjen iz study_plan logike)
    streak = _calc_streak(current_user.id, db)

    # Danas
    today = date.today()
    today_attempts = (
        db.query(QuizAttempt)
        .filter(
            QuizAttempt.user_id == current_user.id,
            func.date(QuizAttempt.completed_at) == today,
        )
        .count()
    )

    # Ove nedelje
    week_start = today - timedelta(days=today.weekday())
    week_attempts = (
        db.query(QuizAttempt)
        .filter(
            QuizAttempt.user_id == current_user.id,
            func.date(QuizAttempt.completed_at) >= week_start,
        )
        .count()
    )

    return {
        "total_attempts": total_attempts,
        "passed_attempts": passed_attempts,
        "pass_rate": round(
            (passed_attempts / total_attempts * 100) if total_attempts else 0, 1
        ),
        "avg_score": avg_score,
        "total_quizzes": total_quizzes,
        "total_documents": total_documents,
        "completed_plan_items": completed_plan_items,
        "current_streak": streak,
        "today_attempts": today_attempts,
        "week_attempts": week_attempts,
    }


# ────────────────────────────────────────────────────────────────────────────────
# GET /analytics/me/activity
# ────────────────────────────────────────────────────────────────────────────────
@router.get("/me/activity")
async def get_activity(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Dnevna aktivnost (broj završenih kvizova) za zadnjih N dana."""
    if days > 90:
        days = 90

    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    # Grupisanje po datumu
    rows = (
        db.query(
            func.date(QuizAttempt.completed_at).label("day"),
            func.count(QuizAttempt.id).label("count"),
            func.avg(QuizAttempt.percentage).label("avg_pct"),
        )
        .filter(
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.completed_at is not None,
            func.date(QuizAttempt.completed_at) >= start_date,
            func.date(QuizAttempt.completed_at) <= end_date,
        )
        .group_by(func.date(QuizAttempt.completed_at))
        .all()
    )

    # Mapiraj u dict za brzo lookup
    data_map = {
        str(r.day): {"count": r.count, "avg_pct": round(float(r.avg_pct or 0), 1)}
        for r in rows
    }

    # Popuni sve dane (i prazne = 0)
    result = []
    current = start_date
    while current <= end_date:
        key = str(current)
        entry = data_map.get(key, {"count": 0, "avg_pct": 0.0})
        result.append(
            {
                "date": key,
                "count": entry["count"],
                "avg_pct": entry["avg_pct"],
            }
        )
        current += timedelta(days=1)

    return {"days": days, "data": result}


# ────────────────────────────────────────────────────────────────────────────────
# GET /analytics/me/quizzes
# ────────────────────────────────────────────────────────────────────────────────
@router.get("/me/quizzes")
async def get_quiz_performance(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Performanse po kvizovima — broj pokušaja, prosečan score, zadnji pokušaj."""
    quizzes = (
        db.query(Quiz)
        .filter(
            Quiz.user_id == current_user.id,
            Quiz.status == "ready",
        )
        .all()
    )

    result = []
    for quiz in quizzes:
        attempts = (
            db.query(QuizAttempt)
            .filter(
                QuizAttempt.quiz_id == quiz.id,
                QuizAttempt.user_id == current_user.id,
                QuizAttempt.completed_at is not None,
            )
            .all()
        )

        if not attempts:
            continue

        avg_pct = sum(a.percentage for a in attempts) / len(attempts)
        best_pct = max(a.percentage for a in attempts)
        last_attempt = max(attempts, key=lambda a: a.completed_at)

        result.append(
            {
                "quiz_id": str(quiz.id),
                "quiz_title": quiz.title,
                "attempt_count": len(attempts),
                "avg_score": round(avg_pct, 1),
                "best_score": round(best_pct, 1),
                "last_attempt_at": last_attempt.completed_at.isoformat(),
                "last_passed": last_attempt.passed,
            }
        )

    # Sortiraj po broju pokušaja (najpopularniji prvi)
    result.sort(key=lambda x: x["attempt_count"], reverse=True)
    return {"quizzes": result[:limit]}


# ────────────────────────────────────────────────────────────────────────────────
# GET /analytics/me/documents
# ────────────────────────────────────────────────────────────────────────────────
@router.get("/me/documents")
async def get_document_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Statistike po dokumentima — broj kvizova, pokušaja."""
    docs = db.query(Document).filter(Document.user_id == current_user.id).all()

    result = []
    for doc in docs:
        quizzes = db.query(Quiz).filter(Quiz.document_id == doc.id).all()

        quiz_ids = [q.id for q in quizzes]
        attempt_count = 0
        if quiz_ids:
            attempt_count = (
                db.query(QuizAttempt)
                .filter(
                    QuizAttempt.quiz_id.in_(quiz_ids),
                    QuizAttempt.user_id == current_user.id,
                    QuizAttempt.completed_at is not None,
                )
                .count()
            )

        result.append(
            {
                "document_id": str(doc.id),
                "document_title": doc.title,
                "status": doc.status,
                "quiz_count": len(quizzes),
                "attempt_count": attempt_count,
                "created_at": doc.created_at.isoformat(),
            }
        )

    result.sort(key=lambda x: x["attempt_count"], reverse=True)
    return {"documents": result}


# ────────────────────────────────────────────────────────────────────────────────
# GET /analytics/me/streak-history
# ────────────────────────────────────────────────────────────────────────────────
@router.get("/me/streak-history")
async def get_streak_history(
    weeks: int = 8,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aktivnost po nedeljama — heatmap podaci."""
    end_date = date.today()
    start_date = end_date - timedelta(weeks=weeks)

    rows = (
        db.query(
            func.date(QuizAttempt.completed_at).label("day"),
            func.count(QuizAttempt.id).label("count"),
        )
        .filter(
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.completed_at is not None,
            func.date(QuizAttempt.completed_at) >= start_date,
        )
        .group_by(func.date(QuizAttempt.completed_at))
        .all()
    )

    return {
        "weeks": weeks,
        "data": [{"date": str(r.day), "count": r.count} for r in rows],
    }


# ────────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────────
def _calc_streak(user_id, db: Session) -> int:
    """Broj uzastopnih dana sa barem jednim završenim kvizom."""
    today = date.today()
    streak = 0
    check = today
    # Ako danas nema pokušaja, počni od juče
    today_count = (
        db.query(QuizAttempt)
        .filter(
            QuizAttempt.user_id == user_id,
            func.date(QuizAttempt.completed_at) == today,
        )
        .count()
    )
    if today_count == 0:
        check = today - timedelta(days=1)

    for _ in range(365):
        count = (
            db.query(QuizAttempt)
            .filter(
                QuizAttempt.user_id == user_id,
                func.date(QuizAttempt.completed_at) == check,
            )
            .count()
        )
        if count == 0:
            break
        streak += 1
        check -= timedelta(days=1)

    return streak
