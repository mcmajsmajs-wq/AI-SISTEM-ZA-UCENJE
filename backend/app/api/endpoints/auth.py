# -*- coding: utf-8 -*-
"""
================================================================================
AUTHENTICATION ENDPOINTS
================================================================================
Endpoint-i za autentikaciju korisnika.

Verzija: 1.0.0
================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.db.session import get_db
from app.schemas.auth import Token, UserLogin, UserRegister, UserResponse
from app.db.models.user import User
from app.services.auth import AuthService, get_current_user, get_current_active_user
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
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
        full_name=user_data.full_name,
    )

    logger.info(f"User registered successfully: {user.email}")

    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
    )


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    ================================================================================
    LOGIN KORISNIKA
    ================================================================================
    Autentikuje korisnika i vraća JWT token.

    Args:
        user_data: UserLogin sa email i password
        db: Database session

    Returns:
        Token sa access_token i token_type

    Raises:
        HTTPException 401: Ako su kredencijali netačni
    ================================================================================
    """
    logger.info(f"Login attempt for user: {user_data.email}")

    user = AuthService.authenticate_user(
        db=db, email=user_data.email, password=user_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Kreiranje token-a
    access_token = AuthService.create_access_token(data={"sub": str(user.id)})

    refresh_token = AuthService.create_refresh_token(data={"sub": str(user.id)})

    logger.info(f"User logged in successfully: {user.email}")

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token,
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
        db=db, email=user_data.email, password=user_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = AuthService.create_access_token(data={"sub": str(user.id)})

    refresh_token = AuthService.create_refresh_token(data={"sub": str(user.id)})

    logger.info(f"User logged in successfully: {user.email}")

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token,
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    ================================================================================
    LOGOUT KORISNIKA
    ================================================================================
    Invalidira trenutni JWT token.

    Note: Za potpuni logout, token treba dodati u blacklist (Redis).
    Trenutno samo vraća uspešnu poruku.
    ================================================================================
    """
    logger.info(f"Logout for user: {current_user.email}")

    # TODO: Implementirati token blacklist u Redis
    # Trenutno samo vraćamo uspešnu poruku
    # Token će isteći prirodno nakon expires_in vremena

    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    refresh_token: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    REFRESH TOKEN
    ================================================================================
    Generiše novi access token koristeći refresh token.

    Args:
        refresh_token: Validan refresh token (query parameter ili JSON body)

    Returns:
        Novi Token

    Raises:
        HTTPException 401: Ako je refresh token invalid
    ================================================================================
    """
    # Support both query parameter and JSON body
    if refresh_token is None:
        try:
            body = await request.json()
            refresh_token = body.get("refresh_token")
        except (ValueError, KeyError):
            pass

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="refresh_token is required",
        )

    logger.info("Token refresh attempt")

    # Dekodiranje refresh token-a
    payload = AuthService.decode_token(refresh_token)

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
    new_access_token = AuthService.create_access_token(data={"sub": str(user.id)})

    new_refresh_token = AuthService.create_refresh_token(data={"sub": str(user.id)})

    logger.info(f"Token refreshed for user: {user.email}")

    return Token(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=new_refresh_token,
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
        created_at=current_user.created_at,
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
