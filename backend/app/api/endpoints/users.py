# -*- coding: utf-8 -*-
"""
================================================================================
USERS ENDPOINTS
================================================================================
Endpoint-i za upravljanje korisnicima.

Verzija: 1.0.0
================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from pydantic import BaseModel
from typing import Optional as _Optional
import logging

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.document import Document, Chunk
from app.db.models.quiz import QuizAttempt
from app.schemas.user import UserResponse, UserUpdate, UserStats
from app.services.auth import get_current_user, AuthService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    ================================================================================
    GET CURRENT USER
    ================================================================================
    Vraća podatke trenutno ulogovanog korisnika.
    ================================================================================
    """
    logger.debug(f"Fetching current user data: {current_user.email}")

    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    UPDATE CURRENT USER
    ================================================================================
    Ažurira podatke trenutno ulogovanog korisnika.
    ================================================================================
    """
    logger.info(f"Updating user data for: {current_user.email}")

    # Ažuriranje polja koja su prosleđena
    if user_data.full_name is not None:
        current_user.full_name = user_data.full_name

    if user_data.timezone is not None:
        current_user.timezone = user_data.timezone

    if user_data.language is not None:
        current_user.language = user_data.language

    db.commit()
    db.refresh(current_user)

    logger.info(f"User updated successfully: {current_user.email}")

    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
    )


@router.put("/me/password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    CHANGE PASSWORD
    ================================================================================
    Menja password trenutno ulogovanog korisnika.
    ================================================================================
    """
    logger.info(f"Password change request for: {current_user.email}")

    # Verifikacija trenutnog password-a
    if not AuthService.verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Hash novog password-a
    current_user.hashed_password = AuthService.get_password_hash(new_password)

    db.commit()

    logger.info(f"Password changed successfully for: {current_user.email}")

    return {"message": "Password changed successfully"}


@router.get("/me/stats", response_model=UserStats)
async def get_user_stats(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    ================================================================================
    GET USER STATISTICS
    ================================================================================
    Vraća statistiku korisnika (dokumenti, kvizovi, skor).
    ================================================================================
    """
    logger.debug(f"Fetching user statistics for: {current_user.email}")

    uid = current_user.id

    # Documents & chunks
    total_documents = (
        db.query(func.count(Document.id)).filter(Document.user_id == uid).scalar() or 0
    )

    chunk_stats = (
        db.query(
            func.count(Chunk.id).label("total"),
            func.sum(Chunk.is_translated).label("translated"),
        )
        .join(Document, Chunk.document_id == Document.id)
        .filter(Document.user_id == uid)
        .first()
    )
    total_chunks = int(chunk_stats.total or 0)
    translated_chunks = int(chunk_stats.translated or 0)

    # Quiz attempts
    attempts = db.query(QuizAttempt).filter(QuizAttempt.user_id == uid).all()
    total_quizzes_taken = len([a for a in attempts if a.completed_at is not None])
    if attempts:
        scores = [
            a.score / a.total_points * 100
            for a in attempts
            if (a.total_points or 0) > 0 and a.completed_at
        ]
        average_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    else:
        average_score = 0.0

    # Calculate study streak from ALL attempts (including partial) by started_at date
    activity_dates_raw = (
        db.query(func.date(QuizAttempt.started_at))
        .filter(QuizAttempt.user_id == uid)
        .distinct()
        .all()
    )
    streak = 0
    if activity_dates_raw:
        today = date.today()
        parsed = set()
        for (d,) in activity_dates_raw:
            if d is None:
                continue
            if isinstance(d, str):
                d = date.fromisoformat(d)
            parsed.add(d)
        check = today
        for _ in range(len(parsed) + 1):
            if check in parsed:
                streak += 1
                check -= timedelta(days=1)
            else:
                break

    return UserStats(
        total_documents=total_documents,
        total_chunks=total_chunks,
        translated_chunks=translated_chunks,
        total_quizzes_taken=total_quizzes_taken,
        average_score=average_score,
        total_study_time_minutes=0,
        current_streak_days=streak,
        longest_streak_days=streak,
        study_streak=streak,
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    ================================================================================
    DELETE CURRENT USER
    ================================================================================
    Briše nalog trenutno ulogovanog korisnika (soft delete).
    ================================================================================
    """
    logger.warning(f"User account deletion requested: {current_user.email}")

    # Soft delete - deaktiviramo nalog
    current_user.is_active = False

    # TODO: Implementirati GDPR compliant brisanje podataka
    # TODO: Zakazati hard delete nakon X dana

    db.commit()

    logger.info(f"User account deactivated: {current_user.email}")

    return None


# ================================================================================
# AI SETTINGS ENDPOINTS
# ================================================================================


class AISettingsRequest(BaseModel):
    ai_provider: str = "auto"  # auto | ollama | openai | claude | gemini | groq | mistral | deepseek | custom
    ai_api_key_openai: _Optional[str] = None
    ai_api_key_claude: _Optional[str] = None
    ai_api_key_gemini: _Optional[str] = None
    ai_api_key_groq: _Optional[str] = None
    ai_api_key_mistral: _Optional[str] = None
    ai_api_key_deepseek: _Optional[str] = None
    ai_custom_base_url: _Optional[str] = None
    ai_api_key_custom: _Optional[str] = None


class AISettingsResponse(BaseModel):
    ai_provider: str
    has_openai_key: bool = False
    has_claude_key: bool = False
    has_gemini_key: bool = False
    has_groq_key: bool = False
    has_mistral_key: bool = False
    has_deepseek_key: bool = False
    has_custom_key: bool = False
    openai_key_preview: _Optional[str] = None
    claude_key_preview: _Optional[str] = None
    gemini_key_preview: _Optional[str] = None
    groq_key_preview: _Optional[str] = None
    mistral_key_preview: _Optional[str] = None
    deepseek_key_preview: _Optional[str] = None
    custom_base_url: _Optional[str] = None
    custom_key_preview: _Optional[str] = None


@router.get("/me/ai-settings", response_model=AISettingsResponse)
async def get_ai_settings(current_user: User = Depends(get_current_user)):
    """Vraća AI podešavanja korisnika."""

    def preview(key):
        if key and len(key) > 8:
            return "..." + key[-4:]
        return None

    return AISettingsResponse(
        ai_provider=current_user.ai_provider or "auto",
        has_openai_key=bool(current_user.ai_api_key_openai),
        has_claude_key=bool(current_user.ai_api_key_claude),
        has_gemini_key=bool(current_user.ai_api_key_gemini),
        has_groq_key=bool(current_user.ai_api_key_groq),
        has_mistral_key=bool(current_user.ai_api_key_mistral),
        has_deepseek_key=bool(current_user.ai_api_key_deepseek),
        has_custom_key=bool(current_user.ai_api_key_custom),
        openai_key_preview=preview(current_user.ai_api_key_openai),
        claude_key_preview=preview(current_user.ai_api_key_claude),
        gemini_key_preview=preview(current_user.ai_api_key_gemini),
        groq_key_preview=preview(current_user.ai_api_key_groq),
        mistral_key_preview=preview(current_user.ai_api_key_mistral),
        deepseek_key_preview=preview(current_user.ai_api_key_deepseek),
        custom_base_url=current_user.ai_custom_base_url,
        custom_key_preview=preview(current_user.ai_api_key_custom),
    )


@router.put("/me/ai-settings", response_model=AISettingsResponse)
async def update_ai_settings(
    data: AISettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Čuva AI podešavanja korisnika."""
    valid_providers = {
        "auto",
        "ollama",
        "openai",
        "claude",
        "gemini",
        "groq",
        "mistral",
        "deepseek",
        "custom",
    }
    if data.ai_provider not in valid_providers:
        raise HTTPException(
            status_code=400, detail=f"Nevažeći provajder. Dozvoljeni: {valid_providers}"
        )

    current_user.ai_provider = data.ai_provider

    # Always update keys if provided (including empty strings to clear them)
    def update_key(field, value):
        # Update if value is not None (allow empty strings to clear key)
        if value is not None:
            setattr(current_user, field, value if value else None)
            logger.info(f"Updating {field}: {str(value)[:10] if value else 'cleared'}")

    update_key("ai_api_key_openai", data.ai_api_key_openai)
    update_key("ai_api_key_claude", data.ai_api_key_claude)
    update_key("ai_api_key_gemini", data.ai_api_key_gemini)
    update_key("ai_api_key_groq", data.ai_api_key_groq)
    update_key("ai_api_key_mistral", data.ai_api_key_mistral)
    update_key("ai_api_key_deepseek", data.ai_api_key_deepseek)
    update_key("ai_custom_base_url", data.ai_custom_base_url)
    update_key("ai_api_key_custom", data.ai_api_key_custom)

    db.commit()
    db.refresh(current_user)
    logger.info(
        f"AI settings updated for {current_user.email}: provider={data.ai_provider}"
    )

    def preview(key):
        if key and len(key) > 8:
            return "..." + key[-4:]
        return None

    return AISettingsResponse(
        ai_provider=current_user.ai_provider,
        has_openai_key=bool(current_user.ai_api_key_openai),
        has_claude_key=bool(current_user.ai_api_key_claude),
        has_gemini_key=bool(current_user.ai_api_key_gemini),
        has_groq_key=bool(current_user.ai_api_key_groq),
        has_mistral_key=bool(current_user.ai_api_key_mistral),
        has_custom_key=bool(current_user.ai_api_key_custom),
        openai_key_preview=preview(current_user.ai_api_key_openai),
        claude_key_preview=preview(current_user.ai_api_key_claude),
        gemini_key_preview=preview(current_user.ai_api_key_gemini),
        groq_key_preview=preview(current_user.ai_api_key_groq),
        mistral_key_preview=preview(current_user.ai_api_key_mistral),
        custom_base_url=current_user.ai_custom_base_url,
        custom_key_preview=preview(current_user.ai_api_key_custom),
    )
