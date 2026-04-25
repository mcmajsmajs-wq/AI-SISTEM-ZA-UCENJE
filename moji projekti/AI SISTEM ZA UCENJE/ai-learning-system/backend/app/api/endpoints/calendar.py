# -*- coding: utf-8 -*-
"""
===============================================================================
CALENDAR ENDPOINTS
===============================================================================
Endpoint-i za kalendar i sistem ponavljanja.

Verzija: 1.0.0
===============================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.document import Document
from app.db.models.quiz import Quiz, QuizAttempt
from app.services.auth import get_current_user
from app.services.calendar import calendar_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/weekly")
async def get_weekly_calendar(
    start_date: Optional[str] = Query(None, description="ISO datum početka nedelje"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    GET WEEKLY CALENDAR
    ================================================================================
    Vraća nedeljni kalendar sa dostupnim slotovima.
    ================================================================================
    """
    if start_date:
        try:
            start = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use ISO format."
            )
    else:
        start = datetime.now()
    
    calendar = calendar_service.get_weekly_availability(
        user_id=current_user.id,
        start_date=start
    )
    
    return {
        "data": calendar
    }


@router.get("/due")
async def get_due_reviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    GET DUE REVIEWS
    ================================================================================
    Vraća stavke koje treba danas ponoviti.
    ================================================================================
    """
    quiz_attempts = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == current_user.id,
        QuizAttempt.completed_at.isnot(None)
    ).all()
    
    items = []
    
    for attempt in quiz_attempts:
        quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
        
        if quiz:
            items.append({
                'item_type': 'quiz',
                'item_id': quiz.id,
                'title': quiz.title,
                'next_review': (attempt.completed_at + timedelta(days=1)).isoformat(),
                'ease_factor': 2.5,
                'interval': 1,
                'repetitions': 0,
            })
    
    due_items = calendar_service.get_due_items(items)
    
    return {
        "data": {
            "due_today": len(due_items),
            "items": due_items
        }
    }


@router.get("/schedule/{document_id}")
async def get_study_schedule(
    document_id: int,
    sessions: int = Query(7, ge=1, le=30, description="Broj sesija"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    GET STUDY SCHEDULE
    ================================================================================
    Generiše raspored učenja za dokument.
    ================================================================================
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    schedule = calendar_service.generate_study_schedule(
        document_title=document.title,
        num_sessions=sessions
    )
    
    return {
        "data": {
            "document_id": document_id,
            "document_title": document.title,
            "schedule": schedule
        }
    }


@router.get("/streak")
async def get_streak_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    GET STREAK INFO
    ================================================================================
    Vraća informacije o seriji uzastopnih dana učenja.
    ================================================================================
    """
    quiz_attempts = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == current_user.id,
        QuizAttempt.completed_at.isnot(None)
    ).all()
    
    sessions = [
        {
            'completed_at': attempt.completed_at.isoformat()
        }
        for attempt in quiz_attempts
    ]
    
    streak_info = calendar_service.calculate_streak(sessions)
    
    return {
        "data": streak_info
    }


@router.post("/review/{item_type}/{item_id}")
async def submit_review(
    item_type: str,
    item_id: int,
    quality: int = Query(..., ge=0, le=5, description="Kvalitet odgovora (0-5)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    SUBMIT REVIEW
    ================================================================================
    Podnosi ocenu za stavku i računa sledeći interval ponavljanja.
    ================================================================================
    """
    if item_type not in ['quiz', 'document']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item type. Use 'quiz' or 'document'."
        )
    
    if quality < 0 or quality > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quality must be between 0 and 5."
        )
    
    ease_factor = 2.5
    interval = 1
    repetitions = 0
    
    new_ease, new_interval, new_reps = calendar_service.calculate_next_review(
        quality=quality,
        ease_factor=ease_factor,
        interval=interval,
        repetitions=repetitions
    )
    
    next_review = datetime.now() + timedelta(days=new_interval)
    
    return {
        "data": {
            "item_type": item_type,
            "item_id": item_id,
            "ease_factor": new_ease,
            "interval": new_interval,
            "repetitions": new_reps,
            "next_review": next_review.isoformat(),
            "quality": quality,
        }
    }


@router.get("/today")
async def get_today_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    GET TODAY SUMMARY
    ================================================================================
    Vraća današnji pregled učenja.
    ================================================================================
    """
    today = datetime.now().date()
    
    quiz_attempts_today = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == current_user.id,
        QuizAttempt.completed_at >= today
    ).all()
    
    documents = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.deleted_at.is_(None)
    ).all()
    
    completed_quizzes = len([a for a in quiz_attempts_today if a.passed])
    
    return {
        "data": {
            "date": today.isoformat(),
            "completed_quizzes": completed_quizzes,
            "total_documents": len(documents),
            "due_reviews": 0,
            "study_time_minutes": completed_quizzes * 10,
        }
    }
