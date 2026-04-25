# -*- coding: utf-8 -*-
"""
================================================================================
PYDANTIC SCHEMAS - USERS
================================================================================
Verzija: 1.0.0
================================================================================
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    """User creation model."""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """User update model."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)


class UserResponse(UserBase):
    """User response model."""
    id: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserStats(BaseModel):
    """User statistics model."""
    total_documents: int = 0
    total_chunks: int = 0
    translated_chunks: int = 0
    total_quizzes_taken: int = 0
    average_score: float = 0.0
    total_study_time_minutes: int = 0
    current_streak_days: int = 0
    longest_streak_days: int = 0
    study_streak: int = 0  # alias for current_streak_days (frontend compat)
    
    class Config:
        from_attributes = True
