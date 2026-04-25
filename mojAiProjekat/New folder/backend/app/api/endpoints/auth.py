# -*- coding: utf-8 -*-
"""
================================================================================
AUTHENTICATION ENDPOINTS
================================================================================
Endpoint-i za autentikaciju korisnika.

Verzija: 1.0.0
================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging
import secrets
import hashlib
from datetime import datetime, timedelta

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.session import get_db
from app.schemas.auth import Token, UserLogin, UserRegister, UserResponse
from app.db.models.user import User
from app.services.auth import AuthService, get_current_user, get_current_active_user
from app.services.email_service import email_service
from app.core.config import settings

limiter = Limiter(key_func=get_remote_address)

# ────────────────────────────────────────────────────────────────────────────────
# In-memory token store (production: migrate to Redis)
# ────────────────────────────────────────────────────────────────────────────────
_reset_tokens: dict[str, dict] = {}   # token_hash → {user_id, expires_at}


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

router = APIRouter()
logger = logging.getLogger(__name__)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserRegister, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    ================================================================================
    REGISTRACIJA KORISNIKA
    ================================================================================
    Kreira novog korisnika u sistemu.
    
    Args:
        user_data: Podaci za registraciju (email, password, full_name)
        db: Database session
    
    Returns:
        UserResponse sa podacima kreiranog korisnika
    
    Raises:
        HTTPException 400: Ako email već postoji
    ================================================================================
    """
    logger.info(f"Registration attempt for email: {user_data.email}")
    
    user = AuthService.create_user(
        db=db,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name
    )
    
    logger.info(f"User registered successfully: {user.email}")

    # Šalji welcome email u pozadini (ne blokira response)
    background_tasks.add_task(email_service.send_welcome, user.email, user.full_name)

    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at
    )


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    ================================================================================
    LOGIN KORISNIKA
    ================================================================================
    Autentikuje korisnika i vraća JWT token.
    
    Args:
        form_data: OAuth2 form data (username, password)
        db: Database session
    
    Returns:
        Token sa access_token i token_type
    
    Raises:
        HTTPException 401: Ako su kredencijali netačni
    ================================================================================
    """
    logger.info(f"Login attempt for user: {form_data.username}")
    
    user = AuthService.authenticate_user(
        db=db,
        email=form_data.username,
        password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Kreiranje token-a
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id)}
    )
    
    refresh_token = AuthService.create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    logger.info(f"User logged in successfully: {user.email}")
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token
    )


@router.post("/login/json", response_model=Token)
async def login_json(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    ================================================================================
    LOGIN KORISNIKA (JSON)
    ================================================================================
    Alternativni login endpoint koji prihvata JSON umesto form data.
    
    Args:
        user_data: UserLogin sa email i password
        db: Database session
    
    Returns:
        Token sa access_token i token_type
    ================================================================================
    """
    logger.info(f"JSON login attempt for user: {user_data.email}")
    
    user = AuthService.authenticate_user(
        db=db,
        email=user_data.email,
        password=user_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id)}
    )
    
    refresh_token = AuthService.create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    logger.info(f"User logged in successfully: {user.email}")
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    ================================================================================
    LOGOUT KORISNIKA
    ================================================================================
    Invalidira trenutni JWT token dodavanjem u Redis blacklist.
    ================================================================================
    """
    logger.info(f"Logout for user: {current_user.email}")
    
    # Dodaj token u blacklist
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        AuthService.blacklist_token(token)
    
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: Optional[RefreshTokenRequest] = None,
    refresh_token_query: Optional[str] = Query(None, alias="refresh_token"),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    REFRESH TOKEN
    ================================================================================
    Generiše novi access token koristeći refresh token.
    
    Args:
        refresh_token: Validan refresh token (can be sent as JSON body or query param)
    
    Returns:
        Novi Token
    
    Raises:
        HTTPException 401: Ako je refresh token invalid
    """
    token = refresh_data.refresh_token if refresh_data else refresh_token_query
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="refresh_token is required"
        )
    
    logger.info("Token refresh attempt")
    
    # Dekodiranje refresh token-a
    payload = AuthService.decode_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Provera tipa token-a
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Dohvatanje korisnika
    user = AuthService.get_user_by_id(db, user_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Kreiranje novog access token-a
    new_access_token = AuthService.create_access_token(
        data={"sub": str(user.id)}
    )
    
    new_refresh_token = AuthService.create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    logger.info(f"Token refreshed for user: {user.email}")
    
    return Token(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=new_refresh_token
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    ================================================================================
    GET CURRENT USER INFO
    ================================================================================
    Vraća podatke o trenutno ulogovanom korisniku.
    ================================================================================
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at
    )


@router.post("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """
    ================================================================================
    VERIFY EMAIL
    ================================================================================
    Verifikuje email adresu korisnika.
    
    TODO: Implementirati email verification flow
    ================================================================================
    """
    # TODO: Implementirati pravi email verification
    # Trenutno placeholder
    
    return {"message": "Email verification not yet implemented"}


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(
    http_request: Request,
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    FORGOT PASSWORD
    ================================================================================
    Šalje email sa linkom za reset lozinke.
    Token važi 1 sat. Uvek vraća 200 (sigurnosna praksa).
    ================================================================================
    """
    user = db.query(User).filter(User.email == request.email).first()

    if user and user.is_active:
        # Generiši token i sačuvaj hash
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        _reset_tokens[token_hash] = {
            "user_id": str(user.id),
            "expires_at": datetime.utcnow() + timedelta(hours=1),
        }
        logger.info(f"Password reset token generated for: {user.email}")

        # Pošalji email u pozadini
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={raw_token}"
        background_tasks.add_task(
            email_service.send_password_reset, user.email, user.full_name, reset_link
        )

    # Uvek isti response (ne otkrivamo da li email postoji)
    return {"message": "Ako email postoji, poslali smo link za reset lozinke."}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    ================================================================================
    RESET PASSWORD
    ================================================================================
    Prima token iz emaila i postavlja novu lozinku.
    Token se briše nakon upotrebe (single-use).
    ================================================================================
    """
    token_hash = hashlib.sha256(request.token.encode()).hexdigest()
    token_data = _reset_tokens.get(token_hash)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nevažeći ili istekli token za reset lozinke.",
        )

    if datetime.utcnow() > token_data["expires_at"]:
        _reset_tokens.pop(token_hash, None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token za reset lozinke je istekao. Zatražite novi.",
        )

    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Korisnik nije pronađen.",
        )

    # Postavi novu lozinku i obriši token
    user.hashed_password = AuthService.get_password_hash(request.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()
    _reset_tokens.pop(token_hash, None)

    logger.info(f"Password reset successful for: {user.email}")
    return {"message": "Lozinka uspešno promenjena. Možete se prijaviti."}
