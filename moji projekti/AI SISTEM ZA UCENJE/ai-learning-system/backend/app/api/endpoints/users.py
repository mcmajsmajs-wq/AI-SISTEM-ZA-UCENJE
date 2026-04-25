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
from typing import List
import logging

from app.db.session import get_db
from app.db.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserStats
from app.services.auth import get_current_user, get_current_active_user, AuthService

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
        created_at=current_user.created_at
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
        created_at=current_user.created_at
    )


@router.put("/me/password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
            detail="Current password is incorrect"
        )
    
    # Hash novog password-a
    current_user.hashed_password = AuthService.get_password_hash(new_password)
    
    db.commit()
    
    logger.info(f"Password changed successfully for: {current_user.email}")
    
    return {"message": "Password changed successfully"}


@router.get("/me/stats", response_model=UserStats)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    GET USER STATISTICS
    ================================================================================
    Vraća statistiku korisnika (dokumenti, kvizovi, skor).
    ================================================================================
    """
    logger.debug(f"Fetching user statistics for: {current_user.email}")
    
    # TODO: Implementirati prave statistike iz baze
    # Trenutno vraćamo placeholder vrednosti
    
    return UserStats(
        total_documents=0,
        total_quizzes_taken=0,
        average_score=0.0,
        total_study_time_minutes=0,
        current_streak_days=0,
        longest_streak_days=0
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
