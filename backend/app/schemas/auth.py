# -*- coding: utf-8 -*-
"""
================================================================================
PYDANTIC SCHEMAS - AUTHENTICATION
================================================================================
Verzija: 1.0.0
================================================================================
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class Token(BaseModel):
    """JWT Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: Optional[str] = Field(None, description="Refresh token for getting new access token")


class UserLogin(BaseModel):
    """User login request model."""
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserRegister(BaseModel):
    """User registration request model."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: str = Field(..., min_length=2, max_length=255)


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: EmailStr
    full_name: str
    is_active: bool
    is_verified: bool = False
    created_at: datetime

    class Config:
        from_attributes = True
