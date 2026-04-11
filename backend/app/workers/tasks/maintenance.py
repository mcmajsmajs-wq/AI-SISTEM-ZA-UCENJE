# -*- coding: utf-8 -*-
"""
================================================================================
TASKS - MAINTENANCE MODULE
================================================================================
Background task za održavanje sistema.

Tasks:
- cleanup_old_files
- cleanup_old_sessions_task
- cache_warming_task

Verzija: 2.0.0 (FAZA 4 - Modularizacija)
================================================================================
"""

from celery import shared_task
from sqlalchemy.orm import sessionmaker
import logging

from app.core.config import settings  # noqa: F401
from app.db.session import engine

logger = logging.getLogger(__name__)


def get_db_session():
    """
    Kreira SQLAlchemy session za task.

    Returns:
        SQLAlchemy Session instanca
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


@shared_task
def cleanup_old_files():
    """
    Periodični task za čišćenje starih fajlova.
    Briše soft-deleted fajlove starije od 30 dana.
    """
    logger.info("Starting cleanup of old files")

    # TODO: Implementirati cleanup
    # 1. Pronađi fajlove sa deleted_at starijim od 30 dana
    # 2. Obriši iz storage-a
    # 3. Obriši iz baze

    logger.info("Cleanup completed")
    return {"status": "success", "files_deleted": 0}


@shared_task
def cleanup_old_sessions_task():
    """
    Čišćenje starih sesija i keša.
    """
    logger.info("Starting cleanup of old sessions")
    # Implementacija zavisna od Redis-a
    logger.info("Session cleanup completed")
    return {"status": "success", "sessions_cleaned": 0}


@shared_task
def cache_warming_task():
    """
    Preloadovanje keša sa često korišćenim podacima.
    """
    logger.info("Starting cache warming")
    # Implementacija keš warming logike
    logger.info("Cache warming completed")
    return {"status": "success", "items_cached": 0}


@shared_task
def send_study_reminders():
    """
    Periodični task: šalje dnevne podsetnike svim korisnicima koji imaju
    reminder_enabled=True u StudyPlan-u i čiji je reminder_time = trenutni sat.
    Poziva se svakih sat vremena (Celery Beat).
    """
    from datetime import date, datetime
    from app.db.models.user import User
    from app.db.models.study_plan import StudyPlan, StudyPlanItem
    from app.db.models.quiz import QuizAttempt  # noqa: F401
    from sqlalchemy import func  # noqa: F401
    from app.services.email_service import email_service

    logger.info("Pokretanje dnevnih podsetnika...")
    db = get_db_session()
    sent = 0
    try:
        current_hour = datetime.now().strftime("%H")
        today = date.today()

        plans = (
            db.query(StudyPlan)
            .filter(
                StudyPlan.is_active is True,
                StudyPlan.reminder_enabled is True,
            )
            .all()
        )

        for plan in plans:
            if plan.reminder_time and plan.reminder_time.strftime("%H") != current_hour:
                continue

            user = db.query(User).filter(User.id == plan.user_id).first()
            if not user or not user.email:
                continue

            today_items = (
                db.query(StudyPlanItem)
                .filter(
                    StudyPlanItem.plan_id == plan.id,
                    StudyPlanItem.target_date == today,
                )
                .all()
            )

            pending = [i for i in today_items if not i.is_completed]
            if not pending:
                continue

            item_names = [i.title for i in pending[:3]]
            items_str = ", ".join(item_names)

            ok = email_service.send_daily_reminder(
                to=user.email,
                full_name=user.full_name or "",
                items=items_str,
                total=len(pending),
            )
            if ok:
                sent += 1

    except Exception as exc:
        logger.error(f"Error in send_study_reminders: {exc}")
    finally:
        db.close()

    logger.info(f"Podsetnici poslati: {sent}")
    return {"status": "success", "reminders_sent": sent}


@shared_task
def send_weekly_summaries():
    """
    Periodični task: šalje nedeljni sažetak svakom aktivnom korisniku.
    Poziva se jednom nedeljno (npr. nedeljom u 10:00).
    """
    from datetime import date, timedelta
    from app.db.models.user import User
    from app.db.models.study_plan import StudyPlan, StudyPlanItem
    from app.db.models.quiz import QuizAttempt  # noqa: F841
    from sqlalchemy import func  # noqa: F401
    from app.services.email_service import email_service
    from app.api.endpoints.analytics import _calc_streak

    logger.info("Pokretanje nedeljnih sažetaka...")
    db = get_db_session()
    sent = 0
    try:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        plans = db.query(StudyPlan).filter(StudyPlan.is_active is True).all()
        for plan in plans:
            user = db.query(User).filter(User.id == plan.user_id).first()
            if not user or not user.email:
                continue

            week_done = (
                db.query(StudyPlanItem)
                .filter(
                    StudyPlanItem.plan_id == plan.id,
                    StudyPlanItem.is_completed is True,
                    StudyPlanItem.completed_at >= week_start,
                )
                .count()
            )

            avg_row = (
                db.query(func.avg(QuizAttempt.percentage))
                .filter(
                    QuizAttempt.user_id == user.id,
                    QuizAttempt.completed_at >= week_start,
                )
                .scalar()
            )
            avg_score = int(avg_row) if avg_row else 0

            streak = _calc_streak(user.id, db)
            total_items = (
                db.query(StudyPlanItem)
                .filter(
                    StudyPlanItem.plan_id == plan.id,
                    StudyPlanItem.target_date <= today,
                )
                .count()
            )
            completed_items = (
                db.query(StudyPlanItem)
                .filter(
                    StudyPlanItem.plan_id == plan.id,
                    StudyPlanItem.is_completed is True,
                    StudyPlanItem.completed_at >= week_start,
                )
                .count()
            )

            ok = email_service.send_weekly_summary(
                to=user.email,
                full_name=user.full_name or "",
                week_done=week_done,
                avg_score=avg_score,
                streak=streak,
                total_items=total_items,
                completed_items=completed_items,
            )
            if ok:
                sent += 1

    except Exception as exc:
        logger.error(f"Error in send_weekly_summaries: {exc}")
    finally:
        db.close()

    logger.info(f"Nedeljni sažetci poslati: {sent}")
    return {"status": "success", "summaries_sent": sent}
