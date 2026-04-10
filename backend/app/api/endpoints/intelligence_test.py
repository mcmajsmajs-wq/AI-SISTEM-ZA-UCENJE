# -*- coding: utf-8 -*-
"""
================================================================================
INTELLIGENCE TEST ENDPOINTS
================================================================================
Endpoint-i za test inteligencije.

Verzija: 1.0.0
================================================================================
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict
from datetime import datetime
import logging

from app.db.session import get_db
from app.db.models.user import User
from app.services.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


class IntelligenceTestResult(BaseModel):
    """Rezultat testa inteligencije."""

    total_questions: int
    correct_answers: int
    time_spent: int
    category_scores: Dict[str, int]


class IntelligenceTestResultResponse(BaseModel):
    """Response za rezultat testa inteligencije."""

    id: int
    user_id: str
    total_questions: int
    correct_answers: int
    time_spent: int
    category_scores: Dict[str, int]
    estimated_iq: int
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/results", response_model=dict)
async def save_test_result(
    result: IntelligenceTestResult,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    ================================================================================
    SAVE TEST RESULT
    ================================================================================
    Čuva rezultat testa inteligencije.
    ================================================================================
    """
    logger.info(f"Saving intelligence test result for user: {current_user.email}")

    # Izračunaj procenjeni IQ
    base_iq = 100
    correct_bonus = (result.correct_answers / result.total_questions) * 40
    time_efficiency = max(0, 1 - (result.time_spent / 600))
    time_bonus = time_efficiency * 20
    estimated_iq = min(160, int(base_iq + correct_bonus + time_bonus))

    # Za sada vraćamo rezultat bez čuvanja u bazu
    # Može se dodati model za čuvanje u budućnosti
    return {
        "success": True,
        "estimated_iq": estimated_iq,
        "total_questions": result.total_questions,
        "correct_answers": result.correct_answers,
        "time_spent": result.time_spent,
        "category_scores": result.category_scores,
        "message": "Rezultat je uspešno izračunat",
    }


@router.get("/results", response_model=dict)
async def get_test_results(
    current_user: User = Depends(get_current_user), db=Depends(get_db)
):
    """
    ================================================================================
    GET TEST RESULTS
    ================================================================================
    Vraća istoriju rezultata testa inteligencije.
    ================================================================================
    """
    logger.info(f"Getting intelligence test results for user: {current_user.email}")

    # Za sada vraćamo praznu listu - može se implementirati cuvanje u bazu
    return {"results": [], "total": 0}
