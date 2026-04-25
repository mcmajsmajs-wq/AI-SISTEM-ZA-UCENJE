# -*- coding: utf-8 -*-
"""
================================================================================
Petar II Petrović-Njegoš
"Blago tome ko dovijek živi, imao se rašta i roditi"
================================================================================

AI Learning System
Authentication Service
Verzija: 1.0.0
Autor: Branko Suznjevic
Datum: 2026

Funkcionalnosti:
- JWT token management
- Password hashing
- User authentication
================================================================================
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

import redis as redis_client
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.db.models.user import User

logger = logging.getLogger(__name__)

# Redis client za token blacklist
_redis = None

def get_redis():
    global _redis
    if _redis is None:
        try:
            _redis = redis_client.from_url(settings.REDIS_CONNECTION_URL, decode_responses=True)
            _redis.ping()
        except Exception as e:
            logger.warning(f"Redis nije dostupan za blacklist: {e}")
            _redis = None
    return _redis

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=True
)

class AuthService:
    """AUTH SERVICE
    ================================================================================
    Centralizovani servis za sve operacije vezane za autentikaciju.
    ================================================================================"""
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Kreira JWT access token.
        
        Args:
            data: Podaci za encoding (obično {"sub": user_id})
            expires_delta: Optional custom expiration time
        
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Kreira JWT refresh token.
        
        Args:
            data: Podaci za encoding (obično {"sub": user_id})
            expires_delta: Optional custom expiration time
        
        Returns:
            Encoded JWT refresh token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """Dekodira JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            Decoded payload ili None ako je token invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.warning(f"JWT decode error: {e}")
            return None
    
    @staticmethod
    def blacklist_token(token: str) -> None:
        r = get_redis()
        if r is None:
            return
        try:
            payload = AuthService.decode_token(token)
            if payload:
                exp = payload.get("exp", 0)
                ttl = max(int(exp - datetime.utcnow().timestamp()), 1)
                r.setex(f"blacklist:{token}", ttl, "1")
        except Exception as e:
            logger.warning(f"Greška pri blacklistingu tokena: {e}")
    
    @staticmethod
    def is_token_blacklisted(token: str) -> bool:
        r = get_redis()
        if r is None:
            return False
        try:
            return r.exists(f"blacklist:{token}") == 1
        except Exception as e:
            logger.warning(f"Greška pri proveri blackliste: {e}")
            return False
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Dohvata korisnika po email adresi.
        
        Args:
            db: Database session
            email: Email adresa korisnika
        
        Returns:
            User objekat ili None
        """
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Dohvata korisnika po ID-u.
        
        Args:
            db: Database session
            user_id: UUID korisnika
        
        Returns:
            User objekat ili None
        """
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Autentikuje korisnika sa email-om i password-om.
        
        Args:
            db: Database session
            email: Email adresa
            password: Plain text password
        
        Returns:
            User objekat ako je autentikacija uspešna, None inače
        """
        user = AuthService.get_user_by_email(db, email)
        
        if not user:
            logger.warning(f"User not found: {email}")
            return None
        
        if not user.is_active:
            logger.warning(f"User account disabled: {email}")
            return None
        
        if not AuthService.verify_password(password, user.hashed_password):
            logger.warning(f"Invalid password for user: {email}")
            return None
        
        return user
    
    @staticmethod
    def create_user(
        db: Session,
        email: str,
        password: str,
        full_name: str
    ) -> User:
        """Kreira novog korisnika.
        
        Args:
            db: Database session
            email: Email adresa
            password: Plain text password
            full_name: Puno ime korisnika
        
        Returns:
            Kreirani User objekat
        
        Raises:
            HTTPException: Ako email već postoji
        """
        # Provera da li email već postoji
        existing_user = AuthService.get_user_by_email(db, email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Kreiranje korisnika
        hashed_password = AuthService.get_password_hash(password)
        
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
            is_verified=False
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"Created new user: {email}")
        
        return user

# ================================================================================
# DEPENDENCY ZA DOBIJANJE TRENUTNOG KORISNIKA
# ================================================================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """FastAPI dependency za dobijanje trenutno ulogovanog korisnika.
    
    Koristi se u endpoint-ima koji zahtevaju autentikaciju.
    
    Args:
        token: JWT token iz Authorization header-a
        db: Database session
    
    Returns:
        User objekat trenutnog korisnika
    
    Raises:
        HTTPException: 401 ako je token invalid ili korisnik ne postoji
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Provera blackliste
    if AuthService.is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token je poništen. Molimo prijavite se ponovo.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Dekodiranje token-a
    payload = AuthService.decode_token(token)
    
    if payload is None:
        raise credentials_exception
    
    # Provera tipa token-a
    if payload.get("type") != "access":
        raise credentials_exception
    
    # Dohvatanje user_id iz token-a
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Dohvatanje korisnika iz baze
    user = AuthService.get_user_by_id(db, user_id)
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency koja dodatno proverava da li je korisnik aktivan.
    
    Args:
        current_user: User iz get_current_user dependency
    
    Returns:
        User objekat ako je aktivan
    
    Raises:
        HTTPException: 403 ako korisnik nije aktivan
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

async def get_current_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency koja proverava da li je korisnik verifikovan.
    
    Koristi se za endpoint-e koji zahtevaju verifikovan nalog.
    
    Args:
        current_user: User iz get_current_user dependency
    
    Returns:
        User objekat ako je verifikovan
    
    Raises:
        HTTPException: 403 ako korisnik nije verifikovan
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first."
        )
    return current_user

# ================================================================================
# OPTIONAL USER DEPENDENCY (ne baca grešku ako nema token-a)
# ================================================================================

async def get_optional_user(
    token: Optional[str] = Depends(OAuth2PasswordBearer(
        tokenUrl=f"{settings.API_V1_STR}/auth/login",
        auto_error=False
    )),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Dependency koja vraća korisnika ako postoji token, ali ne baca grešku.
    
    Korisno za endpoint-e koji rade drugačije za ulogovane/neulogovane.
    
    Args:
        token: Optional JWT token
        db: Database session
    
    Returns:
        User objekat ili None
    """
    if token is None:
        return None
    
    try:
        payload = AuthService.decode_token(token)
        if payload is None or payload.get("type") != "access":
            return None
        
        user_id = payload.get("sub")
        if user_id is None:
            return None
        
        return AuthService.get_user_by_id(db, user_id)
    except Exception:
        return None
