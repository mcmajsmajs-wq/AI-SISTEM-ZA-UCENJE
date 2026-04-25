# -*- coding: utf-8 -*-
"""
===============================================================================
ANALYTICS ENDPOINTS
===============================================================================
Endpoint-i za analitiku i statistike.

Verzija: 1.0.0
===============================================================================
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.db.session import get_db
from app.db.models.user import User
from app.services.auth import get_current_user
from app.services.analytics import analytics_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/overview")
async def get_user_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    GET USER OVERVIEW
    ================================================================================
    Vraća pregled korisnikovih aktivnosti.
    ================================================================================
    """
    overview = analytics_service.get_user_overview(
        user_id=current_user.id,
        db=db
    )
    
    return {"data": overview}


@router.get("/activity")
async def get_activity_timeline(
    days: int = Query(30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    GET ACTIVITY TIMELINE
    ================================================================================
    Vraća timeline aktivnosti.
    ================================================================================
    """
    timeline = analytics_service.get_activity_timeline(
        user_id=current_user.id,
        days=days,
        db=db
    )
    
    return {"data": timeline}


@router.get("/progress")
async def get_learning_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    GET LEARNING PROGRESS
    ================================================================================
    Vraća progres učenja.
    ================================================================================
    """
    progress = analytics_service.get_learning_progress(
        user_id=current_user.id,
        db=db
    )
    
    return {"data": progress}


@router.get("/quizzes")
async def get_quiz_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    GET QUIZ ANALYTICS
    ================================================================================
    Vraća analitiku kvizova.
    ================================================================================
    """
    analytics = analytics_service.get_quiz_analytics(
        user_id=current_user.id,
        db=db
    )
    
    return {"data": analytics}


@router.get("/documents")
async def get_document_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    GET DOCUMENT ANALYTICS
    ================================================================================
    Vraća analitiku dokumenata.
    ================================================================================
    """
    analytics = analytics_service.get_document_analytics(
        user_id=current_user.id,
        db=db
    )
    
    return {"data": analytics}


@router.get("/insights")
async def get_study_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    GET STUDY INSIGHTS
    ================================================================================
    Vraća uvide za učenje.
    ================================================================================
    """
    insights = analytics_service.get_study_insights(
        user_id=current_user.id,
        db=db
    )
    
    return {"data": insights}


@router.get("/dashboard")
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    GET DASHBOARD METRICS
    ================================================================================
    Vraća metrike za dashboard.
    ================================================================================
    """
    metrics = analytics_service.get_dashboard_metrics(
        user_id=current_user.id,
        db=db
    )
    
    return {"data": metrics}
